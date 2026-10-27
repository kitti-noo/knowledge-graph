# knowledge-graph

Playground สำหรับลองทำ Knowledge Graph + GraphRAG ด้วย Ollama (local) + NetworkX ไม่ต้องใช้ Docker

## RAG vs GraphRAG

| | Vector RAG | GraphRAG (โปรเจกต์นี้) |
|---|---|---|
| Ingest | chunk → embed → vector DB | chunk → **LLM extract triples** → graph |
| หน่วยข้อมูล | chunk ของข้อความ | `(subject) -[RELATION]-> (object)` |
| Retrieve | top-k similarity | หา seed entity → เดิน k-hop รอบๆ |
| เก่งเรื่อง | "ข้อความไหนพูดถึง X" | คำถาม multi-hop, ความสัมพันธ์, การ aggregate |

## Pipeline

```
text ──chunk──▶ LLM (extract.py) ──triples──▶ graph.py (NetworkX) ──▶ data/graph.json
                                                     │
question ──▶ find seed entities ──▶ k-hop subgraph ──▶ facts ──▶ LLM answer (query.py)
```

## Run

```bash
uv sync
uv run main.py ingest data/sample.txt
uv run main.py stats
uv run main.py viz                       # เปิด data/graph.html ดูกราฟ
uv run main.py ask "Which Nobel Prize did the daughter of Polonium's discoverer win?" -v
```

เปลี่ยน model: `KG_MODEL=qwen3:8b uv run main.py ...`

## ลองต่อ (เรียงจากง่าย → ยาก)

1. **Entity resolution** — ตอนนี้ merge แค่ lowercase ดูใน `stats` จะเห็น "Curie" กับ "Marie Curie" แยกกัน ลองใช้ embedding similarity หรือให้ LLM ตัดสิน
2. **Schema** — fix ชุด entity type / relation ใน prompt (ontology) จะได้กราฟสะอาดขึ้นมาก
3. **Hybrid** — ใช้ vector search หา seed entity แทน LLM แล้วแนบ chunk ต้นฉบับ (`source_chunk`) ไปกับ facts
4. **Neo4j** — `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none neo4j` แล้วเขียน triples เป็น Cypher `MERGE` จะ query ได้ เช่น `MATCH p=shortestPath(...)`
5. **Community summaries** — แบบ Microsoft GraphRAG: `nx.community.louvain_communities` → ให้ LLM สรุปแต่ละกลุ่ม → ตอบคำถามระดับภาพรวม ("ธีมหลักของเอกสารคืออะไร")
