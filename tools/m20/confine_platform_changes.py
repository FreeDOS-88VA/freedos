#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""M20 helper: confine PC-88VA edits of shared component files to PC88VA builds.

For each FILE, compute its non-PC-88VA view (PC88VA, PC88VA_M13 and
M13_VISIBLE_DIAGNOSTICS undefined), compare it with the baseline version
(comments and whitespace ignored), and wrap every remaining difference as

    #if defined(PC88VA)      (%ifdef PC88VA in NASM)
    <current lines>
    #else
    <baseline lines>
    #endif

so the non-PC-88VA preprocessed text equals the baseline by construction.
Run it inside a component checkout as

    confine_platform_changes.py BASE_REVISION FILE...

then review the result, tidy it where needed, and verify with
`tools/m20/pc_baseline.py` (byte identity of the non-PC-88VA build).
It is a development aid that edits component source; it is not a build input.
"""
import difflib, re, subprocess, sys
from pathlib import Path

FALSE_IF = [r'#\s*if\s+defined\s*\(\s*PC88VA\s*\)', r'#\s*ifdef\s+PC88VA\b',
            r'#\s*if\s+defined\s*\(\s*M13_VISIBLE_DIAGNOSTICS\s*\)',
            r'%\s*ifdef\s+(PC88VA|PC88VA_M13|M13_VISIBLE_DIAGNOSTICS)\b']
TRUE_IF = [r'#\s*if\s+!\s*defined\s*\(\s*PC88VA\s*\)\s*$', r'%\s*ifndef\s+PC88VA\b']
FALSE_ELIF = [r'#\s*elif\s+defined\s*\(\s*PC88VA\s*\)']


def kind(line):
    t = line.strip()
    if not t or t[0] not in '#%':
        return None
    m = re.match(r'[#%]\s*(\w+)', t)
    if not m:
        return None
    w = m.group(1)
    if w.startswith('if'):
        return 'if'
    if w in ('else', 'elif', 'elifdef', 'elifndef'):
        return 'else'
    if w == 'endif':
        return 'endif'
    return None


def matches(pats, line):
    return any(re.match(p, line.strip()) for p in pats)


def pc_view(lines):
    """Return [(index, line)] of lines visible in a non-PC-88VA build."""
    out = []
    stack = []  # entries: [mode, emitting_branch]; mode in known/unknown
    def active():
        return all(e[1] for e in stack)
    for i, l in enumerate(lines):
        k = kind(l)
        if k == 'if':
            if matches(FALSE_IF, l):
                stack.append(['known', False]); continue
            if matches(TRUE_IF, l):
                stack.append(['known', True]); continue
            if active():
                out.append((i, l))
            stack.append(['unknown', True]); continue
        if k == 'else' and stack:
            e = stack[-1]
            if e[0] == 'known':
                word = l.strip().lstrip('#%').strip()
                if word.startswith('else'):
                    e[1] = (not e[1]) if e[1] is not None else False
                    if len(e) > 2: e[1] = False
                    continue
                if e[1]:              # taken branch ends: rest is skipped
                    e[1] = False; e.append('done'); continue
                if len(e) > 2:
                    continue
                # untaken known branch followed by #elif X: X decides now
                e[0] = 'unknown'; e[1] = True
                if all(x[1] for x in stack[:-1]):
                    out.append((i, '#if ' + word[4:]))
                continue
            if matches(FALSE_ELIF, l):
                e[1] = False; continue
            e[1] = True
            if all(x[1] for x in stack[:-1]):
                out.append((i, l))
            continue
        if k == 'endif' and stack:
            e = stack.pop()
            if e[0] == 'unknown' and active():
                out.append((i, l))
            continue
        if active():
            out.append((i, l))
    if stack:
        raise ValueError('unbalanced conditionals')
    return out


def norm_c(text_lines):
    """Strip C comments; return normalized line strings."""
    out, incom = [], False
    for l in text_lines:
        s, i, buf = l, 0, ''
        while i < len(s):
            if incom:
                j = s.find('*/', i)
                if j < 0:
                    i = len(s)
                else:
                    incom = False; i = j + 2
            else:
                j = s.find('/*', i); k = s.find('//', i)
                if k >= 0 and (j < 0 or k < j):
                    buf += s[i:k]; break
                if j < 0:
                    buf += s[i:]; break
                buf += s[i:j]; incom = True; i = j + 2
        out.append(re.sub(r'\s+', ' ', buf).strip())
    return out


def norm_asm(text_lines):
    out = []
    for l in text_lines:
        s = l.split(';', 1)[0]
        out.append(re.sub(r'\s+', ' ', s).strip())
    return out


def balanced(lines):
    d = 0
    for l in lines:
        k = kind(l)
        if k == 'if':
            d += 1
        elif k == 'endif':
            d -= 1
            if d < 0:
                return False
        elif k == 'else' and d == 0:
            return False
    return d == 0


def guard(path, base_text):
    raw = path.read_bytes().decode('latin-1')
    nl = '\r\n' if '\r\n' in raw else '\n'
    new = raw.replace('\r\n', '\n').split('\n')
    base = base_text.replace('\r\n', '\n').split('\n')
    asm = path.suffix.lower() in ('.asm', '.inc', '.mac')
    norm = norm_asm if asm else norm_c
    view = pc_view(new)
    vnorm = norm([l for _, l in view])
    bnorm = norm(base)
    # keep only non-empty normalized lines, with maps to original indices
    vmap = [view[j][0] for j, s in enumerate(vnorm) if s]
    vseq = [s for s in vnorm if s]
    bmap = [j for j, s in enumerate(bnorm) if s]
    bseq = [s for s in bnorm if s]
    ops = [o for o in difflib.SequenceMatcher(None, vseq, bseq, autojunk=False).get_opcodes()
           if o[0] != 'equal']
    if not ops:
        return 0
    # Build original spans; merge and balance.
    spans = []
    for tag, i1, i2, j1, j2 in ops:
        spans.append([i1, i2, j1, j2])
    def orig(span):
        i1, i2, j1, j2 = span
        n_lo = vmap[i1 - 1] + 1 if i1 > 0 else 0
        n_hi = vmap[i2] if i2 < len(vmap) else len(new)
        b_lo = bmap[j1 - 1] + 1 if j1 > 0 else 0
        b_hi = bmap[j2] if j2 < len(bmap) else len(base)
        return n_lo, n_hi, b_lo, b_hi
    changed = True
    while changed:
        changed = False
        spans.sort()
        merged = []
        for s in spans:
            if merged and s[0] <= merged[-1][1] + 0 and orig(s)[0] <= orig(merged[-1])[1]:
                m = merged[-1]; m[1] = max(m[1], s[1]); m[3] = max(m[3], s[3]); changed = True
            else:
                merged.append(s)
        spans = merged
        for s in spans:
            n_lo, n_hi, b_lo, b_hi = orig(s)
            if not (balanced(new[n_lo:n_hi]) and balanced(base[b_lo:b_hi])):
                # widen by one equal normalized line on each side
                if s[0] > 0: s[0] -= 1; s[2] -= 1
                if s[1] < len(vmap): s[1] += 1; s[3] += 1
                if s[0] == 0 and s[1] == len(vmap):
                    raise ValueError(f'cannot balance a hunk in {path}')
                changed = True
    IF, ELSE, END = (('%ifdef PC88VA', '%else', '%endif') if asm else
                     ('#if defined(PC88VA)', '#else', '#endif'))
    result, pos = [], 0
    for s in sorted(spans):
        n_lo, n_hi, b_lo, b_hi = orig(s)
        result += new[pos:n_lo]
        # trim leading/trailing blank lines shared by both sides
        result.append(IF)
        result += new[n_lo:n_hi]
        result.append(ELSE)
        result += base[b_lo:b_hi]
        result.append(END)
        pos = n_hi
    result += new[pos:]
    path.write_bytes(nl.join(result).encode('latin-1'))
    return len(spans)


def main():
    base_rev, files = sys.argv[1], sys.argv[2:]
    for f in files:
        base = subprocess.run(['git', 'show', f'{base_rev}:{f}'], capture_output=True)
        if base.returncode:
            print(f'{f}: new file, skipped'); continue
        n = guard(Path(f), base.stdout.decode('latin-1'))
        print(f'{f}: wrapped {n} hunk(s)')


if __name__ == '__main__':
    main()
