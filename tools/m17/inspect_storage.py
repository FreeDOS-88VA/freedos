#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independent FAT/container reader. Never imports the fixture producer."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from contracts import load


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(data, p):
    def u16(at): return int.from_bytes(data[at:at+2], 'little')
    def u32(at): return int.from_bytes(data[at:at+4], 'little')
    phys=p['physical_sector_bytes'];bps=p['logical_sector_bytes']
    count=p['cylinders']*p['heads']*p['sectors_per_track']
    header={'raw':0,'hdi':4096,'vhd':220}[p['container']]
    require(len(data)==header+count*phys,'container length')
    if header==4096:
        require((u32(8),u32(12),u32(16),u32(20),u32(24),u32(28)) ==
                (4096,count*phys,phys,p['sectors_per_track'],p['heads'],p['cylinders']),'HDI geometry')
    if header==220:
        require(data[:8]==b'VHD1.00\0','VHD signature')
        require((u16(140),u16(142),data[144],data[145],u16(146),u32(148)) ==
                (count*phys//1048576,phys,p['sectors_per_track'],p['heads'],p['cylinders'],count),'VHD geometry')
    start=p['partition_start'];total=count*phys//bps-start
    if start:
        require(data[header+510:header+512]==b'\x55\xaa','MBR signature')
        at=header+446
        require(data[at]==0 and data[at+4]==6,'MBR partition type/boot flag')
        require(u32(at+8)==start and u32(at+12)==total,'MBR partition range')
        require(data[at+16:header+510]==bytes(48),'unexpected partition')
    origin=header+start*bps
    require(data[origin+510:origin+512]==b'\x55\xaa','BPB signature')
    nbyte=u16(origin+11);spc=data[origin+13];reserved=u16(origin+14)
    nfats=data[origin+16];roots=u16(origin+17);nsmall=u16(origin+19)
    media=data[origin+21];fatsecs=u16(origin+22);nhuge=u32(origin+32)
    require((nbyte,spc,reserved,nfats,roots,media)==
            (bps,p['sectors_per_cluster'],1,2,p['root_entries'],p['media_descriptor']),'BPB geometry')
    require((nsmall==total and nhuge==0) if total<65536 else (nsmall==0 and nhuge==total),'BPB total')
    require(u32(origin+28)==start,'BPB hidden sectors')
    require((u16(origin+24),u16(origin+26))==(p['sectors_per_track'],p['heads']),'BPB CHS metadata')
    require(u32(origin+39)==p['volume_serial'] and data[origin+43:origin+54]==p['volume_label'].ljust(11).encode(),'volume identity')
    rootsecs=(roots*32+bps-1)//bps
    firstdata=reserved+nfats*fatsecs+rootsecs
    require(0<fatsecs and firstdata<total,'FAT/data extents')
    clusters=(total-firstdata)//spc
    bits=12 if clusters<4085 else 16 if clusters<65525 else 32
    require(bits==p['fat_bits'] and bits!=32,'FAT type by cluster count')
    require((clusters+2)*bits<=fatsecs*bps*8,'undersized FAT')
    foff=origin+reserved*bps;flen=fatsecs*bps;fat=data[foff:foff+flen]
    require(fat==data[foff+flen:foff+2*flen],'FAT mirrors')
    def value(cluster):
        if bits==16:return int.from_bytes(fat[cluster*2:cluster*2+2],'little')
        off=cluster+cluster//2;pair=int.from_bytes(fat[off:off+2],'little')
        return (pair>>4 if cluster&1 else pair)&0xfff
    end=(1<<bits)-8
    require(value(0)==((1<<bits)-256)|media and value(1)>=(1<<bits)-8,'FAT reserved entries')
    owned=set();cb=spc*bps;dataoff=origin+firstdata*bps
    def chain(first):
        out=bytearray();current=first;seen=[]
        while True:
            require(2<=current<clusters+2,'cluster outside data area')
            require(current not in owned,'loop or crosslinked cluster')
            owned.add(current);seen.append(current)
            off=dataoff+(current-2)*cb
            require(off+cb<=origin+total*bps,'cluster extent')
            out.extend(data[off:off+cb]);nxt=value(current)
            if nxt>=end:break
            current=nxt
        return bytes(out),seen
    files={};names=set();last=[]
    def directory(raw,prefix='',selfcluster=0,parentcluster=0):
        nonlocal last
        for at in range(0,len(raw),32):
            e=raw[at:at+32]
            if e[0]==0:break
            require(e[0]!=0xe5 and e[11]!=15,'deleted/LFN entry outside fixture contract')
            name=e[:8].decode('ascii').rstrip();ext=e[8:11].decode('ascii').rstrip()
            name+=('.'+ext if ext else '')
            first=int.from_bytes(e[26:28],'little');size=int.from_bytes(e[28:32],'little')
            if name in ('.','..'):
                require(prefix and e[11]==0x10 and first==(selfcluster if name=='.' else parentcluster),'directory parent')
                continue
            if e[11]==8:
                require(not prefix and e[:11]==p['volume_label'].ljust(11).encode(),'root label')
                continue
            path=prefix+name
            require(path not in names,'duplicate entry');names.add(path)
            payload,allocated=chain(first)
            if e[11]==0x10:
                require(size==0 and not prefix and name=='SUBDIR','unexpected directory')
                require(payload[:11]==b'.          ' and payload[32:43]==b'..         ','dot entries')
                directory(payload,path+'/',first,selfcluster)
            else:
                require(e[11]==0x20 and 0<size<=len(payload) and len(allocated)==(size+cb-1)//cb,'file allocation')
                files[path]=payload[:size]
                if name=='LAST.BIN':last=allocated
    rootoff=foff+2*flen
    directory(data[rootoff:rootoff+rootsecs*bps])
    expected={'README.TXT':b'Public M17 storage fixture. Data only; guest support is not implied.\r\n',
              'PATTERN.BIN':bytes(range(256))*128+b'end',
              'LAST.BIN':b'Last allocatable cluster\r\n'+bytes(range(256))*2,
              'SUBDIR/INNER.TXT':b'Nested directory readback.\r\n'}
    require(files==expected,'independent file readback')
    require(last and last[-1]==clusters+1,'last-cluster coverage')
    require({n for n in range(2,clusters+2) if value(n)!=0}==owned,'orphan allocation')
    return {'fat_sectors':fatsecs,'volume_sectors':total,'container_header_bytes':header,'fat_bits':bits,'clusters':clusters,'volume_offset_bytes':origin,'files':{n:{'size':len(v),'sha256':hashlib.sha256(v).hexdigest()} for n,v in files.items()}}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--profiles',type=Path,required=True);ap.add_argument('--directory',type=Path,required=True)
    args=ap.parse_args();manifest=json.loads((args.directory/'manifest.json').read_text())
    require(set(manifest)=={'schema_version','fixtures'} and manifest['schema_version']==1,'manifest schema')
    profiles=load(args.profiles);rows=manifest['fixtures'];require(len(rows)==len(profiles),'manifest count')
    for p,row in zip(profiles,rows):
        filename=p['name']+'.'+{'raw':'img','hdi':'hdi','vhd':'hdd'}[p['container']]
        require(set(row)=={'name','file','size','sha256','container_header_bytes','volume_offset_bytes','volume_sectors','fat_sectors','clusters','files'},'manifest fields')
        require(row['name']==p['name'] and row['file']==filename,'manifest identity/path')
        data=(args.directory/filename).read_bytes()
        require(row['size']==len(data) and row['sha256']==hashlib.sha256(data).hexdigest(),'image identity')
        result=inspect(data,p)
        require(all(result[key]==row[key] for key in ('fat_sectors','volume_sectors','container_header_bytes')),'manifest extents')
        require(result['files']==row['files'] and result['clusters']==row['clusters'] and result['volume_offset_bytes']==row['volume_offset_bytes'],'manifest semantics')
    print('Independent container, partition, BPB, FAT chain and payload validation passed')


if __name__=='__main__':main()
