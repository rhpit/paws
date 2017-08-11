# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = python -msphinx
SPHINXPROJ    = PAWS
SOURCEDIR     = .
BUILDDIR      = ../../paws-doc
GHPAGES       = $(BUILDDIR)/html

# Put it first so that "make" without argument is like "make help".
help:
	@echo "-- PAWS sphinx documentation --"
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  clean      to clean build doc folder $(BUILDDIR)"
	@echo "  doc        to make html doc available at $(GHPAGES)"
	@echo "  gh-pages   to make doc and push to gh-pages branch live"
	@echo

.PHONY: help Makefile

clean:
	@rm -rf $(BUILDDIR)/*
	@echo "deleted $(BUILDDIR)/*"

prep: clean
	@mkdir -p $(GHPAGES)
	git clone --branch gh-pages git@github.com:rhpit/paws.git $(GHPAGES)
	@echo "gh-pages branch cloned at $(GHPAGES)"

# generate html documentation to separated folder ../../paws-doc/html
doc: prep
	$(SPHINXBUILD) -W -c $(SOURCEDIR) -b html $(SOURCEDIR) $(GHPAGES)
	@echo "Build finished. The HTML pages are in $(GHPAGES)"

# generate html documentation and push to github pages
gh-pages: doc
	cd $(GHPAGES) && git add . 
	cd $(GHPAGES) && git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`"
	cd $(GHPAGES) && git push origin gh-pages
	@echo 
	@echo documentation published to https://rhpit.github.io/paws/

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
#%: Makefile
#	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
