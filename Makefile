.PHONY: build test vet install clean

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
DOCDIR ?= $(PREFIX)/share/doc/hypermesh-cli

build:
	mkdir -p bin
	go build -o bin/hypermesh ./cmd/hypermesh
	go build -o bin/hm ./cmd/hm

vet:
	go vet ./...

test:
	go test ./...

# Terms acceptance is --license accept or HYPERMESH_LICENSE=accept.
# Host install consent (--yes) is a separate choice.
install: build
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 bin/hypermesh $(DESTDIR)$(BINDIR)/hypermesh
	install -m 755 bin/hm $(DESTDIR)$(BINDIR)/hm
	install -d $(DESTDIR)$(DOCDIR)
	install -m 644 LICENSE NOTICE $(DESTDIR)$(DOCDIR)/

clean:
	rm -rf bin
