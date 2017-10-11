# Sphinx Makefile customized for PAWS project

SPHINXOPTS    =
SPHINXBUILD   = python -msphinx
SPHINXPROJ    = PAWS
SOURCEDIR     = .
BUILDDIR      = ../../paws-doc
GHPAGES       = $(BUILDDIR)/html
MANPAGES      = $(BUILDDIR)/man

############################################
# Color definition
############################################
NO_COLOR    = \x1b[0m
OK_COLOR    = \x1b[32;01m
WARN_COLOR  = \x1b[33;01m
ERROR_COLOR = \x1b[31;01m

help:
	@echo
	@echo -e "Usage: $(WARN_COLOR) make target$(NO_COLOR) where $(WARN_COLOR)target$(NO_COLOR) is one of following:"
	@echo
	@echo -e "\t$(WARN_COLOR)clean$(NO_COLOR)      to clean build doc folder $(BUILDDIR)"
	@echo -e "\t$(WARN_COLOR)html$(NO_COLOR)       to make html doc available at $(GHPAGES)"
	@echo -e "\t$(WARN_COLOR)man$(NO_COLOR)        to make manpage available at $(MANPAGES)"
	@echo -e "\t$(WARN_COLOR)doc$(NO_COLOR)        to make man and html"
	@echo -e "\t$(WARN_COLOR)gh-pages$(NO_COLOR)   to make doc and push gh-pages branch to github pages"
	@echo -e "$(NO_COLOR)"
	@echo

.PHONY: help Makefile

clean:
	@rm -rf $(BUILDDIR)/*
	@echo -e "$(OK_COLOR)deleted $(BUILDDIR)/*$(NO_COLOR)"
	@echo

prep: clean
	@mkdir -p $(GHPAGES)
	@mkdir -p $(MANPAGES)
	git clone --branch gh-pages git@github.com:rhpit/paws.git $(GHPAGES)
	@echo "gh-pages branch cloned at $(GHPAGES)"
	@echo -e "$(OK_COLOR)gh-pages branch clone at $(GHPAGES)$(NO_COLOR)"
	@echo

# generate manpage documentation
man:
	$(SPHINXBUILD) -W -c $(SOURCEDIR) -b man $(SOURCEDIR) $(MANPAGES)
	@echo -e "$(OK_COLOR)Build finished. The MAN pages are in $(MANPAGES)$(NO_COLOR)"
	@echo

# generate html documentation
html:
	$(SPHINXBUILD) -W -c $(SOURCEDIR) -b html $(SOURCEDIR) $(GHPAGES)
	@echo -e "$(OK_COLOR)Build finished. The HTML pages are in $(GHPAGES)$(NO_COLOR)"
	@echo

# generate html documentation to separated folder ../../paws-doc/html
doc: prep
	make man
	make html
	@echo
	
# generate html documentation and push to github pages
gh-pages: doc
	cd $(GHPAGES) && git fetch --all
	cd $(GHPAGES) && git add . 
	cd $(GHPAGES) && git commit -m "Generated gh-pages for `git log origin/master -1 --pretty=short --abbrev-commit`"
	cd $(GHPAGES) && git push origin gh-pages
	@echo -e "$(OK_COLOR)documentation published to https://rhpit.github.io/paws/$(NO_COLOR)"	
	@echo -e "$(WARN_COLOR)might take some seconds/minute to update$(NO_COLOR)"
	@echo
