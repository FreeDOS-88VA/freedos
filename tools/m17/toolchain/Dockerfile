FROM ubuntu:22.04@sha256:79676deb51ebb02885b0b9d33788e78a37cf1045ad79d1bb04c6a222c3556b3d

ARG APT_SNAPSHOT=20260827T000000Z
ARG OW_PACKAGE_SIZE
ARG OW_PUBLISHER_MD5
ARG OW_PACKAGE_SHA256

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    WATCOM=/opt/openwatcom-1.9 \
    EDPATH=/opt/openwatcom-1.9/eddat \
    INCLUDE=/opt/openwatcom-1.9/h \
    LIB=/opt/openwatcom-1.9/lib286 \
    PATH=/opt/openwatcom-1.9/binl:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# The first apt transaction bootstraps CA certificates from the same immutable
# snapshot. The temporary peer check exception is removed before normal use;
# package signatures and the Open Watcom publisher checksum remain required.
COPY --from=watcom /open-watcom-c-linux-1.9 /tmp/open-watcom-c-linux-1.9

RUN set -eux; \
    printf '%s\n' \
      "deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/${APT_SNAPSHOT}/ jammy main universe" \
      "deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/${APT_SNAPSHOT}/ jammy-updates main universe" \
      "deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/${APT_SNAPSHOT}/ jammy-security main universe" \
      > /etc/apt/sources.list; \
    apt-get -o Acquire::Check-Valid-Until=false \
      -o Acquire::https::Verify-Peer=false \
      -o Acquire::https::Verify-Host=false update; \
    apt-get -o Acquire::Check-Valid-Until=false \
      -o Acquire::https::Verify-Peer=false \
      -o Acquire::https::Verify-Host=false \
      install -y --no-install-recommends \
      ca-certificates=20260601~22.04.1; \
    update-ca-certificates; \
    apt-get -o Acquire::Check-Valid-Until=false update; \
    apt-get -o Acquire::Check-Valid-Until=false install -y --no-install-recommends \
      bash=5.1-6ubuntu1.1 \
      ca-certificates=20260601~22.04.1 \
      file=1:5.41-3ubuntu0.1 \
      gcc=4:11.2.0-1ubuntu1 \
      libc6-dev=2.35-0ubuntu3.14 \
      make=4.3-4.1build1 \
      nasm=2.15.05-1 \
      python3=3.10.6-1~22.04.1 \
      python3-iso3166=2.0.2-1 \
      python3-phonenumbers=8.12.1-1 \
      unzip=6.0-26ubuntu3 \
      xz-utils=5.2.5-2ubuntu1.1; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    mkdir -p /opt/openwatcom-1.9; \
    test "$(stat -c '%s' /tmp/open-watcom-c-linux-1.9)" = "${OW_PACKAGE_SIZE}"; \
    printf '%s  %s\n' "${OW_PUBLISHER_MD5}" /tmp/open-watcom-c-linux-1.9 | md5sum --check --status; \
    printf '%s  %s\n' "${OW_PACKAGE_SHA256}" /tmp/open-watcom-c-linux-1.9 | sha256sum --check --status; \
    unzip -q /tmp/open-watcom-c-linux-1.9 -d /opt/openwatcom-1.9; \
    find /opt/openwatcom-1.9/binl -type f -exec chmod a+rx {} +; \
    for tool in wcc wcl wmake wlink wasm wlib; do test -x "/opt/openwatcom-1.9/binl/$tool"; done; \
    rm -f /tmp/open-watcom-c-linux-1.9

RUN set -eux; \
    useradd --create-home --home-dir /home/m16 --shell /bin/bash m16; \
    mkdir -p /input /work /output; \
    chown -R m16:m16 /input /work /output /home/m16

USER m16
WORKDIR /work
ENTRYPOINT ["/bin/bash"]
