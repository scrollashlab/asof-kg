import sys, os, tempfile, rdflib, pyshacl
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
from rdflib.namespace import RDF
BASE='ontology/asof-kg.ttl'
def load(extra=None):
    g=rdflib.Graph(); g.parse(BASE)
    if extra: g.parse(extra)
    return g
def shacl(g):
    conforms, rg, txt = pyshacl.validate(g, shacl_graph=g, advanced=True, inference='none', allow_warnings=True)
    msgs=sorted(set(str(o) for o in rg.objects(None, rdflib.URIRef('http://www.w3.org/ns/shacl#resultMessage'))))
    return conforms, msgs
def hermit(g):
    import owlready2
    owlready2.JAVA_EXE='java'
    # drop SHACL triples (not OWL) before reasoning
    SH='http://www.w3.org/ns/shacl#'
    h=rdflib.Graph()
    shape_nodes=set(s for s,p,o in g if str(p).startswith(SH) or str(o).startswith(SH))
    for t in g:
        if t[0] in shape_nodes or str(t[1]).startswith(SH) or str(t[2]).startswith(SH): continue
        h.add(t)
    # remove blank nodes only reachable from shapes
    fd,path=tempfile.mkstemp(suffix='.nt'); os.close(fd); h.serialize(path,format='nt')
    w=owlready2.World(); onto=w.get_ontology('file://'+path).load()
    try:
        with onto: owlready2.sync_reasoner_hermit(w, infer_property_values=True, debug=0)
    except owlready2.base.OwlReadyInconsistentOntologyError:
        return 'INCONSISTENT', w
    return 'CONSISTENT', w
g=load(); print('triples',len(g))
c,m=shacl(g); print('BASE SHACL conforms:',c,m)
st,w=hermit(g); print('BASE HermiT:',st)
if st=='CONSISTENT':
    ex='https://w3id.org/asof-kg/example#'; A='https://w3id.org/asof-kg/ontology#'
    d=w.search_one(iri=ex+'decision-2022-10-15'); print('decision-2022-10-15 types:',[x.name for x in d.is_a])
    s2=w.search_one(iri=ex+'stmt-bebtelovimab-eua-v2')
    print('v2 supersedesTransitively:',[x.name for x in getattr(s2,'supersedesTransitively',[])])
    print('v2 types:',[x.name for x in s2.is_a])
    sw=w.search_one(iri=ex+'share-bq11-weighted')
    cur=[x.name for x in w.search(is_a=w.search_one(iri=A+'CurrentStatement'))]
    old=[x.name for x in w.search(is_a=w.search_one(iri=A+'NoLongerCurrentStatement'))]
    print('inferred CurrentStatement:',sorted(n for n in cur if n!='CurrentStatement'))
    print('inferred NoLongerCurrentStatement:',sorted(n for n in old if n!='NoLongerCurrentStatement'))
    print('weighted supersedesTransitively:',sorted(x.name for x in getattr(sw,'supersedesTransitively',[])))
    nb=w.search_one(iri=ex+'share-bq11-nowcast'); 
    print('nowcast validDisjointFrom:',[x.name for x in getattr(nb,'validDisjointFrom',[])])
for t in sorted(os.listdir('tests/negative')):
    g=load('tests/negative/'+t); c,m=shacl(g); st,_=hermit(g); print(t,'| SHACL conforms:',c,m,'| HermiT:',st)
print('--- positive tests')
g=load('tests/positive/chain-validbefore.ttl'); st,w=hermit(g); print('chain test HermiT:',st)
ex='https://w3id.org/asof-kg/example#'
for n in ['share-bq11-nowcast','share-bq11-nowcast-rev','share-bq11-weighted']:
    i=w.search_one(iri=ex+n); print(n,'validBefore ->',[x.name for x in getattr(i,'validBefore',[])], '| validDisjointFrom ->',[x.name for x in getattr(i,'validDisjointFrom',[])])

# --- OWL API checks (the library Protege uses), via ROBOT, on the FULL file including SHACL triples
import subprocess
ROBOT=['java','-jar',os.environ.get('ROBOT_JAR','tools/robot.jar')]
def robot(*a):
    r=subprocess.run(ROBOT+list(a),capture_output=True,text=True); return r.returncode,(r.stdout+r.stderr)
print('--- OWL API / ROBOT (full file, SHACL triples included)')
rc,out=robot('validate-profile','--profile','DL','--input',BASE,'--output','/tmp/asof-dl-profile.txt')
print('OWL 2 DL profile:', 'IN PROFILE' if rc==0 else 'VIOLATIONS (see /tmp/asof-dl-profile.txt)')
rc,out=robot('reason','--reasoner','HermiT','--input',BASE,'--output','/tmp/asof-reasoned.ttl')
print('ROBOT HermiT (base):','CONSISTENT' if rc==0 else 'FAILED: '+out.strip().splitlines()[0])
for t in sorted(os.listdir('tests/negative')):
    fd,merged=tempfile.mkstemp(suffix='.ttl'); os.close(fd); load('tests/negative/'+t).serialize(merged,format='turtle')
    rc,out=robot('reason','--reasoner','HermiT','--input',merged,'--output','/tmp/asof-test-out.ttl')
    print(t,'| ROBOT HermiT:','CONSISTENT' if rc==0 else ('INCONSISTENT' if 'inconsistent' in out.lower() else 'ERROR: '+out.strip()[:200]))
