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
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# generate html documentation to separated folder paws-doc/html
doc:
	@mkdir -p $(BUILDDIR)
	git clone --branch gh-pages git@github.com:rhpit/paws.git $(BUILDDIR)/html
	make html

# generate html documentation and push to github pages
gh-pages: clean doc
	cd $(GHPAGES) && git add . 
	cd $(GHPAGES) && git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`"
	cd $(GHPAGES) && git push origin gh-pages
	@echo 
	@echo documentation published to https://rhpit.github.io/paws/

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
