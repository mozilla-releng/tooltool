FROM golang:1.14

RUN apt-get update -qq \
    # We need to install tzdata before all of the other packages. Otherwise it will show an interactive dialog that
    # we cannot navigate while building the Docker image.
    && apt-get install -y zstd jq \
    && apt-get clean

RUN GO111MODULE=on CGO_ENABLED=0 go get -tags 'exclude_graphdriver_devicemapper exclude_graphdriver_btrfs containers_image_openpgp' github.com/containers/skopeo/cmd/skopeo@v0.1.41

COPY push_image.sh /usr/local/bin/
RUN chmod a+x /usr/local/bin/push_image.sh
CMD ["push_image.sh"]

VOLUME /workspace
