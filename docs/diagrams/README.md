# Diagrams

| แผนภาพ | เครื่องมือ | อยู่ที่ |
|---|---|---|
| Architecture ทั้งระบบ | [Archify](https://github.com/tt-a1i/archify) v3.2.0 | โฟลเดอร์นี้ → แสดงใน [README](../../README.md#architecture) |
| แผนภาพอื่นใน docs (บทที่ 1, 2, 3, 5, 6) | Mermaid | เขียนตรงในไฟล์ markdown แก้ได้เลย GitHub วาดให้เอง |

## ไฟล์ของ architecture

| ไฟล์ | คืออะไร |
|---|---|
| `architecture.json` | **ต้นฉบับ** แก้ที่ไฟล์นี้ |
| `architecture.svg` | ภาพที่ README แสดงบน GitHub (เปลี่ยนสีตามธีม light/dark ให้อัตโนมัติ) |
| `architecture.html` | แผนภาพแบบ interactive (ซูม · คลิกดูเส้นทาง · สลับธีม) เปิดในเบราว์เซอร์ |

## แก้แผนภาพ architecture

ง่ายที่สุดคือให้ AI ที่ติดตั้ง Archify skill (`npx skills add tt-a1i/archify`) แก้ให้ เช่น "ใช้ Archify แก้ docs/diagrams/architecture.json ให้เพิ่ม X"

ถ้าทำเอง:

```bash
git clone --depth 1 https://github.com/tt-a1i/archify /tmp/archify
A=/tmp/archify/archify/bin/archify.mjs

# 1. แก้ architecture.json แล้วสร้าง HTML ใหม่ (ตรวจ schema + layout + ทดสอบในเบราว์เซอร์ให้)
node $A finalize architecture docs/diagrams/architecture.json docs/diagrams/architecture.html --quality showcase

# 2. เปิด architecture.html → Export → "SVG · Auto" แล้วบันทึกทับ docs/diagrams/architecture.svg
```

ข้อความบนแผนภาพเป็นภาษาไทย แต่ปุ่มของ viewer (Export, Legend ฯลฯ) ยังเป็นภาษาอังกฤษ เพราะ Archify ยังไม่มี UI ภาษาไทย
