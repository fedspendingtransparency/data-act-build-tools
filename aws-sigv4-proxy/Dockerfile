
FROM golang:1.17.7-alpine AS build

RUN apk --update add \
      ca-certificates \
      git

RUN mkdir /aws-sigv4-proxy
WORKDIR /aws-sigv4-proxy
COPY  . .

RUN go env -w GOPROXY=direct

RUN CGO_ENABLED=0 GOOS=linux go build ./cmd/aws-sigv4-proxy

FROM alpine:3
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build /aws-sigv4-proxy/aws-sigv4-proxy ./

ENV PORT_NUM 8080
EXPOSE ${PORT_NUM}

ENTRYPOINT ./aws-sigv4-proxy --port 9200 --host $ENDPOINT --name es --region us-gov-west-1 --role-arn $ASSUME_ROLE