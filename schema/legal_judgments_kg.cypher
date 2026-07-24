// Legal Judgments Knowledge Graph — schema
// Node labels: Judgment, Court, Judge, Statute, Party, Citation
// Edge types:  DECIDED_BY, HEARD_IN, INVOKES_STATUTE, INVOLVES_PARTY, CITES

// --- Constraints / indexes ---
CREATE CONSTRAINT judgment_id IF NOT EXISTS FOR (j:Judgment) REQUIRE j.id IS UNIQUE;
CREATE CONSTRAINT court_id    IF NOT EXISTS FOR (c:Court)    REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT judge_id    IF NOT EXISTS FOR (jd:Judge)   REQUIRE jd.id IS UNIQUE;
CREATE CONSTRAINT statute_id  IF NOT EXISTS FOR (s:Statute)  REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT party_id    IF NOT EXISTS FOR (p:Party)    REQUIRE p.id IS UNIQUE;

// --- Relationship shapes (documentation) ---
// (:Judgment)-[:DECIDED_BY]->(:Judge)
// (:Judgment)-[:HEARD_IN]->(:Court)
// (:Judgment)-[:INVOKES_STATUTE]->(:Statute)
// (:Judgment)-[:INVOLVES_PARTY]->(:Party)
// (:Judgment)-[:CITES]->(:Judgment)   // precedent graph
