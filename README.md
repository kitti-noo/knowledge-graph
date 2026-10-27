# knowledge-graph

Playground สำหรับลองทำ Knowledge Graph + GraphRAG ด้วย Ollama (local) + NetworkX ไม่ต้องใช้ Docker

เริ่มจากศูนย์? อ่าน [docs/ — KG 101](docs/README.md)

## โครงสร้าง

```
kg/, main.py              engine ใช้ร่วมกันทุกโดเมน
examples/
  thai-tourism/           ตัวอย่างสำหรับเรียน: เอกสารข้อความ → LLM → กราฟ (docs บทที่ 1–4)
  retail-demo/            ตัวอย่างระบบค้าปลีก (ข้อมูลสมมติ): ontology + CSV + เอกสาร (docs บทที่ 5–6)
domains/                  โดเมนของคุณเองตอนลองในเครื่อง (gitignore ไว้ ไม่ขึ้น GitHub)
docs/                     KG 101 ภาษาไทย
```

ทุกคำสั่งรับ `--domain <โฟลเดอร์>` (ค่าเริ่มต้นคือ `examples/thai-tourism`) กราฟของแต่ละโดเมนจะเก็บไว้ที่ `<โฟลเดอร์>/graph.json`

## RAG vs GraphRAG

| | Vector RAG | GraphRAG (โปรเจกต์นี้) |
|---|---|---|
| Ingest | chunk → embed → vector DB | chunk → **LLM extract triples** → graph |
| หน่วยข้อมูล | chunk ของข้อความ | `(subject) -[RELATION]-> (object)` |
| Retrieve | top-k similarity | หา seed entity → เดิน k-hop รอบๆ |
| เก่งเรื่อง | "ข้อความไหนพูดถึง X" | คำถาม multi-hop, ความสัมพันธ์, การ aggregate |

## Pipeline

```
text ──chunk──▶ LLM (extract.py) ──triples──▶ graph.py (NetworkX) ──▶ graph.json
                                                     │
question ──▶ find seed entities ──▶ k-hop subgraph ──▶ facts ──▶ LLM answer (query.py)
```

## Run

```bash
uv sync
uv run main.py ingest examples/thai-tourism/sample.txt --reset
uv run main.py stats
uv run main.py viz                       # เปิด examples/thai-tourism/graph.html ดูกราฟ
uv run main.py ask "ประเพณีที่ตรงกับยี่เป็งมีต้นกำเนิดที่จังหวัดใด" -v
uv run main.py eval --hops 4            # ถามทุกข้อใน examples/thai-tourism/questions.md
```

เปลี่ยน model: `KG_MODEL=qwen3:8b uv run main.py ...`

### โดเมนของตัวเอง (ตัวอย่าง: ระบบค้าปลีก)

```bash
uv run main.py ingest-csv --domain examples/retail-demo --reset          # ตาราง → กราฟ (ไม่ใช้ LLM)
uv run main.py ingest     --domain examples/retail-demo examples/retail-demo/docs/*.md
uv run main.py impact     --domain examples/retail-demo "ระบบสมาชิก"       # ถ้า CRM ล่ม กระทบใคร
uv run main.py eval       --domain examples/retail-demo                  # วัดผลกับ questions.md
```

ดูทีละขั้นใน [docs/06-walkthrough.md](docs/06-walkthrough.md)

## ลองต่อ (เรียงจากง่าย → ยาก)

1. **Entity resolution** — ตอนนี้ merge แค่ lowercase ดูใน `stats` จะเห็น "สงกรานต์" กับ "ประเพณีสงกรานต์" หรือ "ภาคอีสาน" กับ "ภาคตะวันออกเฉียงเหนือ" แยกกัน ลองใช้ embedding similarity หรือให้ LLM ตัดสิน
2. **Schema** — fix ชุด entity type / relation ใน prompt (ontology) จะได้กราฟสะอาดขึ้นมาก
3. **Hybrid** — ใช้ vector search หา seed entity แทน LLM แล้วแนบ chunk ต้นฉบับ (`source_chunk`) ไปกับ facts
4. **Neo4j** — `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=none neo4j` แล้วเขียน triples เป็น Cypher `MERGE` จะ query ได้ เช่น `MATCH p=shortestPath(...)`
5. **Community summaries** — แบบ Microsoft GraphRAG: `nx.community.louvain_communities` → ให้ LLM สรุปแต่ละกลุ่ม → ตอบคำถามระดับภาพรวม ("ธีมหลักของเอกสารคืออะไร")
