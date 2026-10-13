import os, rdflib
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
g=rdflib.Graph(); g.parse('ontology/asof-kg.ttl')
Q='''PREFIX asof: <https://w3id.org/asof-kg/ontology#>
PREFIX time: <http://www.w3.org/2006/time#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX biolink: <https://w3id.org/biolink/vocab/>
SELECT ?s ?label ?share WHERE {
  ?s biolink:subject %(subj)s ; asof:hasRecordTime ?rt ; asof:hasValidTime ?vt .
  OPTIONAL { ?s rdfs:label ?label } OPTIONAL { ?s asof:estimatedShare ?share }
  ?rt time:hasBeginning/time:inXSDDateTimeStamp ?rb .
  OPTIONAL { ?rt time:hasEnd/time:inXSDDateTimeStamp ?re }
  ?vt time:hasBeginning/time:inXSDDateTimeStamp ?vb .
  OPTIONAL { ?vt time:hasEnd/time:inXSDDateTimeStamp ?ve }
  BIND (xsd:dateTime("%(k)s") AS ?k) BIND (xsd:dateTime("%(v)s") AS ?v)
  FILTER (xsd:dateTime(STR(?rb)) <= ?k && (!BOUND(?re) || ?k < xsd:dateTime(STR(?re))))
  FILTER (xsd:dateTime(STR(?vb)) <= ?v && (!BOUND(?ve) || ?v < xsd:dateTime(STR(?ve))))
}'''
cases=[('ex:bebtelovimab','2022-11-15T00:00:00-05:00','2022-12-05T00:00:00-05:00'),
       ('ex:bebtelovimab','2022-12-05T00:00:00-05:00','2022-12-05T00:00:00-05:00'),
       ('ex:BQ.1.1','2022-11-15T00:00:00-05:00','2022-11-09T00:00:00-05:00'),
       ('ex:BQ.1.1','2022-11-20T00:00:00-05:00','2022-11-09T00:00:00-05:00'),
       ('ex:BQ.1.1','2022-12-05T00:00:00-05:00','2022-11-09T00:00:00-05:00')]
for subj,k,v in cases:
    q=Q%{'subj':subj.replace('ex:','<https://w3id.org/asof-kg/example#')+'>','k':k,'v':v}
    rows=list(g.query(q))
    print(f'subject={subj} as-of(record)={k[:10]} at(valid)={v[:10]} ->',[ (str(r.s).split('#')[1], str(r.share) if r.share else '') for r in rows] or 'no valid statement')
