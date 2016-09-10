MSG?=update html

GITHUB_PAGES_BRANCH=gh-pages

BASEDIR=$(CURDIR)
OUTPUTDIR=$(BASEDIR)/output

publish:
	mkdir -p $(OUTPUTDIR)
	cp result.json $(OUTPUTDIR)/
	cp index.html $(OUTPUTDIR)/

github: publish
	echo "py3tracker.shaform.com" > $(OUTPUTDIR)/CNAME
	ghp-import -r gh-pages -b $(GITHUB_PAGES_BRANCH) $(OUTPUTDIR) -m "$(MSG)"
	git push origin $(GITHUB_PAGES_BRANCH):gh-pages
