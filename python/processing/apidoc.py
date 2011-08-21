import markdowndoc
import pydoc
import processing

pydoc.text = markdowndoc.MarkdownDoc()

def writeMarkdownAPI():
    toDocument = [processing, processing.moduleinstance, processing.parameters]
    for thing in toDocument:
        fn = "%s.md" % thing.__name__
        print "Writing %s..." % fn
        f = open(fn, 'w')
        md = pydoc.render_doc(thing)
        f.write(md)
        f.close()

if __name__ == "__main__":
    writeMarkdownAPI()
    
