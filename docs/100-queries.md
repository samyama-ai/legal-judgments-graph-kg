# 100 Cypher Queries for the Legal Judgments Knowledge Graph

**589 judgments | 34 judges | 1,102 parties | 446 acts | 2,291 topics | 8,363 relationships**

These queries are organized in five progressive levels that illustrate where relational databases hit their ceiling and where graph databases take over. Schema: `Case`, `Judge`, `Party`, `Act`, `Topic` with `DECIDED`, `PARTY_IN {role}`, `CITES {section}`, `ABOUT`.

| Level | Name | SQL Equivalent | Queries |
|-------|------|----------------|---------|
| 1 | **Foundation** | Single table, GROUP BY | 1--15 |
| 2 | **Relational Joins** | 2-table JOIN | 16--35 |
| 3 | **Multi-hop Traversals** | 3--5 JOINs, self-joins | 36--60 |
| 4 | **Path & Pattern Analytics** | Recursive CTEs, breaks down | 61--80 |
| 5 | **Network Intelligence** | Impossible in SQL | 81--100 |

---

## Level 1: Foundation (SQL-equivalent)

*These queries scan a single node type or edge type. Any RDBMS handles them trivially with a single table and GROUP BY.*

### 1. Judgments by month

```cypher
MATCH (c:Case)
RETURN c.month AS month, count(c) AS judgments
ORDER BY month
```

### 2. Judgments by year

```cypher
MATCH (c:Case)
RETURN c.year AS year, count(c) AS judgments
ORDER BY year
```

### 3. Total judges

```cypher
MATCH (j:Judge)
RETURN count(j) AS judges
```

### 4. Total parties

```cypher
MATCH (p:Party)
RETURN count(p) AS parties
```

### 5. Total acts referenced

```cypher
MATCH (a:Act)
RETURN count(a) AS acts
```

### 6. Total topics

```cypher
MATCH (t:Topic)
RETURN count(t) AS topics
```

### 7. Topics by category

```cypher
MATCH (t:Topic)
RETURN t.category AS category, count(t) AS topics
ORDER BY topics DESC
```

### 8. Judges, alphabetical

```cypher
MATCH (j:Judge)
RETURN j.name AS judge
ORDER BY j.name
```

### 9. Judgments per (year, month)

```cypher
MATCH (c:Case)
RETURN c.year AS year, c.month AS month, count(c) AS judgments
ORDER BY year, month
```

### 10. Cases that have a title vs not

```cypher
MATCH (c:Case)
RETURN c.title IS NOT NULL AND c.title <> "" AS has_title, count(c) AS cases
ORDER BY has_title DESC
```

### 11. Sample of acts

```cypher
MATCH (a:Act)
RETURN a.name AS act
ORDER BY a.name
LIMIT 20
```

### 12. Sample of parties

```cypher
MATCH (p:Party)
RETURN p.name AS party
ORDER BY p.name
LIMIT 20
```

### 13. Number of topic categories

```cypher
MATCH (t:Topic)
RETURN count(DISTINCT t.category) AS categories
```

### 14. Longest / shortest case titles

```cypher
MATCH (c:Case)
WHERE c.title <> ""
RETURN c.title AS title, size(c.title) AS length
ORDER BY length DESC
LIMIT 10
```

### 15. Sample of topics with their category

```cypher
MATCH (t:Topic)
RETURN t.text AS topic, t.category AS category
ORDER BY t.text
LIMIT 20
```

---

## Level 2: Relational Joins (2-table JOIN equivalent)

*One relationship hop — the bread and butter of SQL joins.*

### 16. Most productive judges

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)
RETURN j.name AS judge, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 17. Most-cited acts

```cypher
MATCH (c:Case)-[:CITES]->(a:Act)
RETURN a.name AS act, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 18. Most-cited legal sections

```cypher
MATCH (c:Case)-[r:CITES]->(a:Act)
RETURN a.name AS act, r.section AS section, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 19. Most litigated parties

```cypher
MATCH (p:Party)-[:PARTY_IN]->(c:Case)
RETURN p.name AS party, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 20. Most frequent topics

```cypher
MATCH (c:Case)-[:ABOUT]->(t:Topic)
RETURN t.text AS topic, t.category AS category, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 21. Bench size — judges per case

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)
RETURN c.title AS case_title, count(j) AS judges
ORDER BY judges DESC
LIMIT 10
```

### 22. Acts cited per case

```cypher
MATCH (c:Case)-[:CITES]->(a:Act)
RETURN c.title AS case_title, count(DISTINCT a) AS acts_cited
ORDER BY acts_cited DESC
LIMIT 10
```

### 23. Topics per case

```cypher
MATCH (c:Case)-[:ABOUT]->(t:Topic)
RETURN c.title AS case_title, count(DISTINCT t) AS topics
ORDER BY topics DESC
LIMIT 10
```

### 24. Parties per case

```cypher
MATCH (p:Party)-[:PARTY_IN]->(c:Case)
RETURN c.title AS case_title, count(DISTINCT p) AS parties
ORDER BY parties DESC
LIMIT 10
```

### 25. Party roles breakdown

```cypher
MATCH (:Party)-[r:PARTY_IN]->(:Case)
RETURN r.role AS role, count(*) AS count
ORDER BY count DESC
```

### 26. Judgments citing the Indian Penal Code

```cypher
MATCH (c:Case)-[:CITES]->(a:Act)
WHERE a.name = "Indian Penal Code"
RETURN count(DISTINCT c) AS judgments
```

### 27. Judgments citing the Constitution of India

```cypher
MATCH (c:Case)-[:CITES]->(a:Act)
WHERE a.name = "Constitution of India"
RETURN count(DISTINCT c) AS judgments
```

### 28. Judgments per topic category

```cypher
MATCH (c:Case)-[:ABOUT]->(t:Topic)
RETURN t.category AS category, count(DISTINCT c) AS judgments
ORDER BY judgments DESC
```

### 29. Judges by number of distinct acts they cite

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:CITES]->(a:Act)
RETURN j.name AS judge, count(DISTINCT a) AS distinct_acts
ORDER BY distinct_acts DESC
LIMIT 10
```

### 30. Judges by number of distinct topics covered

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)
RETURN j.name AS judge, count(DISTINCT t) AS distinct_topics
ORDER BY distinct_topics DESC
LIMIT 10
```

### 31. Cases citing the most acts

```cypher
MATCH (c:Case)-[:CITES]->(a:Act)
WITH c, count(DISTINCT a) AS acts
WHERE acts >= 5
RETURN c.title AS case_title, acts
ORDER BY acts DESC
LIMIT 10
```

### 32. Sections cited for a specific act (Indian Penal Code)

```cypher
MATCH (c:Case)-[r:CITES]->(a:Act)
WHERE a.name = "Indian Penal Code"
RETURN r.section AS section, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 15
```

### 33. Parties appearing in more than one case

```cypher
MATCH (p:Party)-[:PARTY_IN]->(c:Case)
WITH p, count(DISTINCT c) AS cases
WHERE cases > 1
RETURN p.name AS party, cases
ORDER BY cases DESC
LIMIT 10
```

### 34. Judges with only a single judgment

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)
WITH j, count(DISTINCT c) AS cases
WHERE cases = 1
RETURN j.name AS judge
ORDER BY j.name
```

### 35. Topic categories and their distinct-topic count

```cypher
MATCH (t:Topic)
RETURN t.category AS category, count(DISTINCT t.text) AS distinct_topics
ORDER BY distinct_topics DESC
```

---

## Level 3: Multi-hop Traversals (3-5 JOINs, self-joins)

*Two-to-three hops and self-joins. In SQL these become tangled multi-join queries; here they stay one readable pattern.*

### 36. Judges who most often sit together

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT c) AS cases_together
ORDER BY cases_together DESC
LIMIT 10
```

### 37. Laws cited together

```cypher
MATCH (a1:Act)<-[:CITES]-(c:Case)-[:CITES]->(a2:Act)
WHERE a1.name < a2.name
RETURN a1.name AS act_a, a2.name AS act_b, count(DISTINCT c) AS cited_together
ORDER BY cited_together DESC
LIMIT 10
```

### 38. Laws spanning the widest range of topics

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
RETURN a.name AS act, count(DISTINCT t.category) AS topic_breadth, count(DISTINCT c) AS cases
ORDER BY topic_breadth DESC, cases DESC
LIMIT 10
```

### 39. A judge's subject-matter focus (topic categories)

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)
WHERE j.name = "Dipak Misra"
RETURN t.category AS category, count(DISTINCT c) AS cases
ORDER BY cases DESC
```

### 40. A judge's most-cited acts

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:CITES]->(a:Act)
WHERE j.name = "Dipak Misra"
RETURN a.name AS act, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 41. Topics most associated with the Indian Penal Code

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
WHERE a.name = "Indian Penal Code"
RETURN t.category AS category, count(DISTINCT c) AS cases
ORDER BY cases DESC
```

### 42. Topics most associated with the Constitution

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
WHERE a.name = "Constitution of India"
RETURN t.category AS category, count(DISTINCT c) AS cases
ORDER BY cases DESC
```

### 43. Judges who decided the most criminal cases

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)
WHERE t.category = "criminal"
RETURN j.name AS judge, count(DISTINCT c) AS criminal_cases
ORDER BY criminal_cases DESC
LIMIT 10
```

### 44. Judges who decided the most constitutional cases

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)
WHERE t.category = "constitutional"
RETURN j.name AS judge, count(DISTINCT c) AS constitutional_cases
ORDER BY constitutional_cases DESC
LIMIT 10
```

### 45. Acts co-cited with the Indian Penal Code

```cypher
MATCH (ipc:Act)<-[:CITES]-(c:Case)-[:CITES]->(a:Act)
WHERE ipc.name = "Indian Penal Code" AND a.name <> ipc.name
RETURN a.name AS co_cited_act, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 46. Parties and the acts invoked in their cases

```cypher
MATCH (p:Party)-[:PARTY_IN]->(c:Case)-[:CITES]->(a:Act)
WHERE p.name CONTAINS "State of"
RETURN p.name AS party, count(DISTINCT a) AS distinct_acts, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 47. Cases citing both IPC and the Code of Criminal Procedure

```cypher
MATCH (c:Case)-[:CITES]->(a1:Act), (c)-[:CITES]->(a2:Act)
WHERE a1.name = "Indian Penal Code" AND a2.name = "Code of Criminal Procedure"
RETURN count(DISTINCT c) AS cases
```

### 48. Cases citing both IPC and the Constitution

```cypher
MATCH (c:Case)-[:CITES]->(a1:Act), (c)-[:CITES]->(a2:Act)
WHERE a1.name = "Indian Penal Code" AND a2.name = "Constitution of India"
RETURN count(DISTINCT c) AS cases
```

### 49. Judge pairs and how many topic categories they share

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)<-[:ABOUT]-(c2:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT t.category) AS shared_categories
ORDER BY shared_categories DESC
LIMIT 10
```

### 50. Sections of the Constitution ranked

```cypher
MATCH (c:Case)-[r:CITES]->(a:Act)
WHERE a.name = "Constitution of India"
RETURN r.section AS article, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 15
```

### 51. Each topic category and its most-cited act

```cypher
MATCH (t:Topic)<-[:ABOUT]-(c:Case)-[:CITES]->(a:Act)
RETURN t.category AS category, a.name AS act, count(DISTINCT c) AS cases
ORDER BY category, cases DESC
```

### 52. A party's cases and the deciding judges

```cypher
MATCH (p:Party)-[:PARTY_IN]->(c:Case)<-[:DECIDED]-(j:Judge)
WHERE p.name CONTAINS "Union of India"
RETURN c.title AS case_title, collect(DISTINCT j.name) AS judges
LIMIT 10
```

### 53. Acts cited in constitutional cases

```cypher
MATCH (c:Case)-[:ABOUT]->(t:Topic), (c)-[:CITES]->(a:Act)
WHERE t.category = "constitutional"
RETURN a.name AS act, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 54. A specific judge's judgments with their topics

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)
WHERE j.name = "T. S. Thakur"
RETURN c.title AS case_title, collect(DISTINCT t.text) AS topics
LIMIT 10
```

### 55. The most versatile judges (most topic categories)

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic)
RETURN j.name AS judge, count(DISTINCT t.category) AS categories
ORDER BY categories DESC
LIMIT 10
```

### 56. Two specific judges' shared cases

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name = "Kurian Joseph" AND j2.name = "Rohinton F. Nariman"
RETURN c.title AS case_title, c.year AS year, c.month AS month
ORDER BY month
```

### 57. Acts common to two specific judges

```cypher
MATCH (j1:Judge)-[:DECIDED]->(:Case)-[:CITES]->(a:Act)<-[:CITES]-(:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name = "Dipak Misra" AND j2.name = "A. K. Sikri"
RETURN a.name AS shared_act, count(DISTINCT a) AS x
ORDER BY a.name
LIMIT 15
```

### 58. Acts appearing across the most cases and topic categories

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN a.name AS act, count(DISTINCT c) AS cases, count(DISTINCT t.category) AS categories
ORDER BY cases DESC
LIMIT 10
```

### 59. Who a judge ruled between (judge → case → parties)

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)<-[:PARTY_IN]-(p:Party)
WHERE j.name = "Dipak Misra"
RETURN c.title AS case_title, collect(DISTINCT p.name) AS parties
LIMIT 10
```

### 60. Topic co-occurrence with a given category

```cypher
MATCH (c:Case)-[:ABOUT]->(t1:Topic), (c)-[:ABOUT]->(t2:Topic)
WHERE t1.category = "criminal" AND t1.category < t2.category
RETURN t2.category AS co_category, count(DISTINCT c) AS cases
ORDER BY cases DESC
```

---

## Level 4: Path & Pattern Analytics (recursive CTEs, breaks down in SQL)

*Multi-hop self-joins and pattern queries. These are where recursive SQL CTEs start to buckle.*

### 61. A judge's bench partners (first degree)

```cypher
MATCH (j:Judge)-[:DECIDED]->(:Case)<-[:DECIDED]-(partner:Judge)
WHERE j.name = "Dipak Misra" AND partner.name <> j.name
RETURN partner.name AS partner, count(*) AS cases_together
ORDER BY cases_together DESC
```

### 62. Partners-of-partners (second-degree bench network)

```cypher
MATCH (j:Judge)-[:DECIDED]->(:Case)<-[:DECIDED]-(p1:Judge)-[:DECIDED]->(:Case)<-[:DECIDED]-(p2:Judge)
WHERE j.name = "Dipak Misra" AND p2.name <> j.name AND p2.name <> p1.name
RETURN p2.name AS second_degree, count(DISTINCT p1) AS via_partners
ORDER BY via_partners DESC
LIMIT 10
```

### 63. Judges connected through a shared party

```cypher
MATCH (j1:Judge)-[:DECIDED]->(:Case)<-[:PARTY_IN]-(p:Party)-[:PARTY_IN]->(:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT p) AS shared_parties
ORDER BY shared_parties DESC
LIMIT 10
```

### 64. Bench pairings ranked with their most common act

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge), (c)-[:CITES]->(a:Act)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, a.name AS act, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 65. Acts that share the most co-citing cases with any other act

```cypher
MATCH (a1:Act)<-[:CITES]-(c:Case)-[:CITES]->(a2:Act)
WHERE a1.name < a2.name
WITH a1, a2, count(DISTINCT c) AS shared
RETURN a1.name AS act_a, a2.name AS act_b, shared
ORDER BY shared DESC
LIMIT 10
```

### 66. Judges linked by a common act they both cite

```cypher
MATCH (j1:Judge)-[:DECIDED]->(:Case)-[:CITES]->(a:Act)<-[:CITES]-(:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT a) AS shared_acts
ORDER BY shared_acts DESC
LIMIT 10
```

### 67. For a category, the judges and acts involved

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[:ABOUT]->(t:Topic), (c)-[:CITES]->(a:Act)
WHERE t.category = "tax"
RETURN j.name AS judge, count(DISTINCT a) AS acts, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 68. Cases sharing 2+ acts with a given case

```cypher
MATCH (c1:Case)-[:CITES]->(a:Act)<-[:CITES]-(c2:Case)
WHERE c1.id = "2016-1-1-17-en.md" AND c1 <> c2
WITH c2, count(DISTINCT a) AS shared_acts
WHERE shared_acts >= 2
RETURN c2.title AS case_title, shared_acts
ORDER BY shared_acts DESC
LIMIT 10
```

### 69. Judge similarity by shared acts (top overlaps)

```cypher
MATCH (j1:Judge)-[:DECIDED]->(:Case)-[:CITES]->(a:Act)<-[:CITES]-(:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
WITH j1, j2, count(DISTINCT a) AS overlap
WHERE overlap >= 20
RETURN j1.name AS judge_a, j2.name AS judge_b, overlap
ORDER BY overlap DESC
```

### 70. A judge's reach — distinct parties across their cases

```cypher
MATCH (j:Judge)-[:DECIDED]->(:Case)<-[:PARTY_IN]-(p:Party)
RETURN j.name AS judge, count(DISTINCT p) AS distinct_parties
ORDER BY distinct_parties DESC
LIMIT 10
```

### 71. Acts central to the criminal docket

```cypher
MATCH (c:Case)-[:ABOUT]->(t:Topic), (c)-[:CITES]->(a:Act)
WHERE t.category = "criminal"
RETURN a.name AS act, count(DISTINCT c) AS criminal_cases
ORDER BY criminal_cases DESC
LIMIT 10
```

### 72. Cases connecting two acts and a topic category

```cypher
MATCH (a1:Act)<-[:CITES]-(c:Case)-[:CITES]->(a2:Act), (c)-[:ABOUT]->(t:Topic)
WHERE a1.name = "Indian Penal Code" AND a2.name = "Code of Criminal Procedure"
RETURN t.category AS category, count(DISTINCT c) AS cases
ORDER BY cases DESC
```

### 73. The act-citation profile of the top bench pair

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge), (c)-[:CITES]->(a:Act)
WHERE j1.name = "Kurian Joseph" AND j2.name = "Rohinton F. Nariman"
RETURN a.name AS act, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 74. The largest bench (case with the most judges)

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)
WITH c, count(DISTINCT j) AS bench
RETURN c.title AS case_title, bench
ORDER BY bench DESC
LIMIT 5
```

### 75. Topic categories that bridge the most acts

```cypher
MATCH (t:Topic)<-[:ABOUT]-(c:Case)-[:CITES]->(a:Act)
RETURN t.category AS category, count(DISTINCT a) AS distinct_acts
ORDER BY distinct_acts DESC
```

### 76. Judges whose dockets overlap most (shared topics)

```cypher
MATCH (j1:Judge)-[:DECIDED]->(:Case)-[:ABOUT]->(t:Topic)<-[:ABOUT]-(:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
WITH j1, j2, count(DISTINCT t) AS shared_topics
WHERE shared_topics >= 15
RETURN j1.name AS judge_a, j2.name AS judge_b, shared_topics
ORDER BY shared_topics DESC
LIMIT 10
```

### 77. Multi-act cases and their topic spread

```cypher
MATCH (c:Case)-[:CITES]->(a:Act)
WITH c, count(DISTINCT a) AS acts
WHERE acts >= 4
MATCH (c)-[:ABOUT]->(t:Topic)
RETURN c.title AS case_title, acts, count(DISTINCT t.category) AS categories
ORDER BY acts DESC
LIMIT 10
```

### 78. Specialist statutes — acts appearing in only one topic category

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
WITH a, count(DISTINCT t.category) AS categories, count(DISTINCT c) AS cases
WHERE categories = 1 AND cases >= 3
RETURN a.name AS act, cases
ORDER BY cases DESC
LIMIT 10
```

### 79. Parties that appear alongside the most distinct judges

```cypher
MATCH (p:Party)-[:PARTY_IN]->(:Case)<-[:DECIDED]-(j:Judge)
RETURN p.name AS party, count(DISTINCT j) AS distinct_judges
ORDER BY distinct_judges DESC
LIMIT 10
```

### 80. Full act profile — cases, sections, co-cited acts

```cypher
MATCH (a:Act)<-[r:CITES]-(c:Case)
WHERE a.name = "Indian Penal Code"
OPTIONAL MATCH (c)-[:CITES]->(other:Act)
WHERE other.name <> a.name
RETURN count(DISTINCT c) AS cases, count(DISTINCT r.section) AS sections, count(DISTINCT other) AS co_cited_acts
```

---

## Level 5: Network Intelligence (impossible in SQL)

*Whole-graph pattern intelligence — collaboration networks, co-citation communities, and full multi-entity context in a single traversal.*

### 81. Judge collaboration network (all pairs, weighted)

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT c) AS weight
ORDER BY weight DESC
LIMIT 25
```

### 82. Act co-citation communities (weighted edges)

```cypher
MATCH (a1:Act)<-[:CITES]-(c:Case)-[:CITES]->(a2:Act)
WHERE a1.name < a2.name
RETURN a1.name AS act_a, a2.name AS act_b, count(DISTINCT c) AS weight
ORDER BY weight DESC
LIMIT 25
```

### 83. Bridging judges — who sits with the most distinct colleagues

```cypher
MATCH (j:Judge)-[:DECIDED]->(:Case)<-[:DECIDED]-(other:Judge)
WHERE other.name <> j.name
RETURN j.name AS judge, count(DISTINCT other) AS distinct_colleagues
ORDER BY distinct_colleagues DESC
LIMIT 10
```

### 84. Most connected act (by distinct co-cited acts)

```cypher
MATCH (a:Act)<-[:CITES]-(:Case)-[:CITES]->(other:Act)
WHERE other.name <> a.name
RETURN a.name AS act, count(DISTINCT other) AS distinct_co_acts
ORDER BY distinct_co_acts DESC
LIMIT 10
```

### 85. Judge degree centrality (distinct colleagues, normalized)

```cypher
MATCH (j:Judge)
OPTIONAL MATCH (j)-[:DECIDED]->(:Case)<-[:DECIDED]-(other:Judge)
WHERE other.name <> j.name
RETURN j.name AS judge, count(DISTINCT other) AS degree
ORDER BY degree DESC
```

### 86. Act degree centrality (distinct co-cited acts)

```cypher
MATCH (a:Act)
OPTIONAL MATCH (a)<-[:CITES]-(:Case)-[:CITES]->(other:Act)
WHERE other.name <> a.name
RETURN a.name AS act, count(DISTINCT other) AS degree
ORDER BY degree DESC
LIMIT 15
```

### 87. Topic-category co-occurrence matrix

```cypher
MATCH (c:Case)-[:ABOUT]->(t1:Topic), (c)-[:ABOUT]->(t2:Topic)
WHERE t1.category < t2.category
RETURN t1.category AS category_a, t2.category AS category_b, count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 15
```

### 88. The bench that spans the widest topic range

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge), (c)-[:ABOUT]->(t:Topic)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT t.category) AS categories, count(DISTINCT c) AS cases
ORDER BY categories DESC, cases DESC
LIMIT 10
```

### 89. Which judge pair cites the most acts together

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge), (c)-[:CITES]->(a:Act)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b, count(DISTINCT a) AS acts, count(DISTINCT c) AS cases
ORDER BY acts DESC
LIMIT 10
```

### 90. Indirect party connections (party → judges → other parties)

```cypher
MATCH (p1:Party)-[:PARTY_IN]->(:Case)<-[:DECIDED]-(:Judge)-[:DECIDED]->(:Case)<-[:PARTY_IN]-(p2:Party)
WHERE p1.name = "Union of India" AND p2.name <> p1.name
RETURN p2.name AS connected_party, count(*) AS strength
ORDER BY strength DESC
LIMIT 10
```

### 91. Statutes shared across topic categories (cross-domain acts)

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)-[:ABOUT]->(t:Topic)
WITH a, count(DISTINCT t.category) AS categories, count(DISTINCT c) AS cases
WHERE categories >= 5
RETURN a.name AS act, categories, cases
ORDER BY categories DESC, cases DESC
LIMIT 10
```

### 92. Judges whose dockets overlap most (shared acts + topics)

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge)
WHERE j1.name < j2.name
OPTIONAL MATCH (c)-[:CITES]->(a:Act)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN j1.name AS judge_a, j2.name AS judge_b,
       count(DISTINCT c) AS cases, count(DISTINCT a) AS acts, count(DISTINCT t) AS topics
ORDER BY cases DESC
LIMIT 10
```

### 93. The most foundational act (breadth + volume + connectivity)

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
OPTIONAL MATCH (c)-[:CITES]->(other:Act) WHERE other.name <> a.name
RETURN a.name AS act, count(DISTINCT c) AS cases,
       count(DISTINCT t.category) AS categories, count(DISTINCT other) AS co_acts
ORDER BY cases DESC
LIMIT 10
```

### 94. Full profile of a judge

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)
WHERE j.name = "Dipak Misra"
OPTIONAL MATCH (c)<-[:PARTY_IN]-(p:Party)
OPTIONAL MATCH (c)-[:CITES]->(a:Act)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN count(DISTINCT c) AS cases, count(DISTINCT p) AS parties,
       count(DISTINCT a) AS acts, count(DISTINCT t.category) AS categories
```

### 95. Full profile of an act

```cypher
MATCH (a:Act)<-[r:CITES]-(c:Case)
WHERE a.name = "Constitution of India"
OPTIONAL MATCH (c)<-[:DECIDED]-(j:Judge)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN count(DISTINCT c) AS cases, count(DISTINCT r.section) AS articles,
       count(DISTINCT j) AS judges, count(DISTINCT t.category) AS categories
```

### 96. Everything about one case, one traversal

```cypher
MATCH (c:Case)
WHERE c.id = "2016-1-1-17-en.md"
OPTIONAL MATCH (c)<-[:DECIDED]-(j:Judge)
OPTIONAL MATCH (c)<-[:PARTY_IN]-(p:Party)
OPTIONAL MATCH (c)-[cr:CITES]->(a:Act)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN c.title AS case_title,
       collect(DISTINCT j.name) AS judges,
       collect(DISTINCT p.name) AS parties,
       collect(DISTINCT a.name) AS acts,
       collect(DISTINCT t.text) AS topics
```

### 97. For the top act, its judges, topics and co-acts together

```cypher
MATCH (a:Act)<-[:CITES]-(c:Case)
WHERE a.name = "Indian Penal Code"
OPTIONAL MATCH (c)<-[:DECIDED]-(j:Judge)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN count(DISTINCT c) AS cases,
       count(DISTINCT j) AS judges,
       collect(DISTINCT t.category) AS categories
```

### 98. Bench pairs and the categories they jointly cover

```cypher
MATCH (j1:Judge)-[:DECIDED]->(c:Case)<-[:DECIDED]-(j2:Judge), (c)-[:ABOUT]->(t:Topic)
WHERE j1.name < j2.name
RETURN j1.name AS judge_a, j2.name AS judge_b,
       collect(DISTINCT t.category) AS shared_categories,
       count(DISTINCT c) AS cases
ORDER BY cases DESC
LIMIT 10
```

### 99. Cross-cut: criminal cases with their acts, sections and bench

```cypher
MATCH (c:Case)-[:ABOUT]->(t:Topic)
WHERE t.category = "criminal"
MATCH (c)-[r:CITES]->(a:Act)
MATCH (c)<-[:DECIDED]-(j:Judge)
RETURN c.title AS case_title, collect(DISTINCT j.name) AS bench,
       collect(DISTINCT a.name + " " + r.section) AS cited
LIMIT 10
```

### 100. The whole graph, one traversal: every citation's full context

```cypher
MATCH (j:Judge)-[:DECIDED]->(c:Case)-[r:CITES]->(a:Act)
OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
RETURN c.title AS case_title, j.name AS judge,
       a.name AS act, r.section AS section, t.category AS category
ORDER BY c.year DESC, c.month
LIMIT 25
```

---

## Bonus: Semantic search (requires `--embed`)

Load with `python -m etl.loader --data-dir data --embed` to attach a summary
embedding to each `Case`, then run semantic k-NN — the in-engine equivalent of the
reference demo's pgvector layer. Query it via the MCP `vector_search` tool or the
engine's vector API (e.g. *"bail conditions in criminal cases"* → semantically
relevant judgments, not just keyword matches).
