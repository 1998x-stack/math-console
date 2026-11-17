# Build from a pinned Manim Community release with Chinese font support.
FROM manimcommunity/manim:v0.19.1
USER root
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk fonts-noto-core && rm -rf /var/lib/apt/lists/*
USER 1000:1000
ENV XDG_CACHE_HOME=/tmp/.cache
