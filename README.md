# Docling + PySpark Distributed Document Processing

A production-ready system for processing PDF documents at scale using Docling and PySpark.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test Without PySpark (No Java needed)
```bash
python test_processor_simple.py
```
✅ **This works now!** Processes PDFs successfully.

### 3. Install Java (Required for PySpark)
```bash
brew install openjdk@11
echo 'export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Run Full PySpark Job
```bash
python scripts/run_spark_job.py
```

### 5. View Results
```bash
python scripts/read_results.py
# or
open output/results.csv
```

## ✅ Status

| Component | Status | Notes |
|-----------|--------|-------|
| PDF Processing | ✅ WORKING | Extracts text, tables, metadata |
| Error Handling | ✅ WORKING | Graceful failure handling |
| Batch Processing | ✅ WORKING | Can process multiple PDFs |
| PySpark Integration | ⏳ NEEDS JAVA | Requires Java 11+ |

## 📁 Project Structure

```
.
├── assets/                     # Test PDFs
│   └── 2206.01062.pdf
├── scripts/
│   ├── docling_module/         # Core processor (no PySpark)
│   │   ├── processor.py        # OOP PDF processor
│   │   └── __init__.py
│   ├── run_spark_job.py        # PySpark integration
│   └── read_results.py         # Results viewer
├── test_processor_simple.py    # Test without PySpark
├── output/                     # Processing results
│   └── results/                # Parquet files
├── requirements.txt
├── STATUS_REPORT.md            # Detailed status
└── README.md                   # This file
```

## 📚 Documentation

- **[STATUS_REPORT.md](STATUS_REPORT.md)** - Detailed status and fixes
- **[processor.py](scripts/docling_module/processor.py)** - Documented source code

## 🎓 Features

- **Object-Oriented Design** - Clean, maintainable code
- **Error Handling** - Graceful failure with detailed messages
- **Type Safety** - Full type hints throughout
- **Distributed Processing** - PySpark UDFs for scale
- **Flexible Configuration** - Easy to customize
- **Multiple Output Formats** - Parquet, CSV, JSON

## 🔧 Requirements

- Python 3.9+
- Java 11+ (for PySpark)
- Docling 2.61.1+
- PySpark 3.5.0+

## 💡 Usage Examples

### Simple Processing
```python
from scripts.docling_module import docling_process

result = docling_process("document.pdf")
if result.success:
    print(result.content)
```

### Advanced Processing
```python
from scripts.docling_module import DocumentProcessorFactory, DocumentConfig

config = DocumentConfig(
    extract_tables=True,
    ocr_enabled=True
)
processor = DocumentProcessorFactory.create_pdf_processor(config)
result = processor.process("document.pdf")
```

### Batch Processing
```python
processor = DocumentProcessorFactory.create_processor_with_defaults()
results = processor.process_directory("path/to/pdfs/")

for result in results:
    if result.success:
        print(f"✅ {result.file_path}: {len(result.content)} chars")
```

## 🐛 Troubleshooting

### "Java Runtime not found"
```bash
brew install openjdk@11
```

### "Cannot import docling_module"
```bash
# Run from project root
python scripts/run_spark_job.py
```

### Results not readable
```bash
python scripts/read_results.py
```

## 📊 Performance

- **Processing Speed**: ~26 seconds per 19-page PDF
- **Output Size**: ~50KB text per document
- **Scalability**: Ready for distributed processing
- **Accuracy**: High-quality text extraction with Docling

## 🎉 What's Working

✅ PDF text extraction  
✅ Metadata extraction  
✅ Error handling  
✅ Batch processing  
✅ OOP design  
✅ Type safety  
✅ Results export (CSV, JSON, Parquet)  

⏳ PySpark distribution (waiting for Java)

## 🚀 Next Steps

1. **Install Java**: `brew install openjdk@11`
2. **Run PySpark job**: `python scripts/run_spark_job.py`
3. **Scale to thousands of documents**
4. **Deploy to Kubernetes** (optional)

---

**Ready to process documents at scale!** 🎯
