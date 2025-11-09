# 🚀 Docling + PySpark: Distributed PDF Processing

A production-ready system for processing PDF documents at scale using Docling and Apache Spark. Extract text, tables, and metadata from thousands of PDFs in parallel.

## ✨ Features

- ✅ **Distributed Processing**: Process thousands of PDFs in parallel using Apache Spark
- ✅ **High-Quality Extraction**: Powered by Docling's modern PDF processing pipeline
- ✅ **Production-Ready**: Comprehensive error handling and fault tolerance
- ✅ **Configurable**: Easily adjust workers, threads, and processing options
- ✅ **Fast**: ~14 seconds per PDF (19 pages) with default settings
- ✅ **Scalable**: Designed to scale from laptop to cloud



## 📋 Table of Contents
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [Configuration](#️-configuration)
- [Performance Tuning](#-performance-tuning)
- [Understanding the Output](#-understanding-the-output)
- [Troubleshooting](#-troubleshooting)
- [Architecture Deep Dive](#-architecture-deep-dive)
- [Future: Kubernetes Deployment](#-future-kubernetes-deployment)



## 🚀 Quick Start

### Prerequisites

```bash
# macOS
brew install openjdk@11

# Ubuntu/Debian
sudo apt-get install openjdk-11-jdk

# Verify installation
java -version
```

### Installation

```bash
# 1. Clone the repository
git clone <your-repo>
cd Docling-Spark-Distributed-Structuring

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run Your First Job

```bash
# Process PDFs with default settings
python scripts/run_spark_job.py
```

**Expected Output:**
```
✅ Spark session created with 4 workers
📂 Found 3 files to process
🔄 Processing files...
✅ 2 PDFs processed successfully
📊 Total content extracted: 1,076,742 characters
💾 Results saved to: output/results.jsonl/
```

## 🏗️ How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  YOUR COMPUTER                                          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  SPARK DRIVER (run_spark_job.py)                │    │
│  │  - Orchestrates everything                      │    │
│  │  - Distributes PDFs to workers                  │    │
│  │  - Collects results                             │    │
│  └─────────────────────────────────────────────────┘    │
│                       │                                 │
│         ┌─────────────┼─────────────┬─────────────┐     │
│         ▼             ▼             ▼             ▼     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Worker 1  │  │Worker 2  │  │Worker 3  │  │Worker 4  │ │
│  │          │  │          │  │          │  │          │ │
│  │Thread 1◯ │  │Thread 1◯ │  │Thread 1◯ │  │Thread 1◯ │ │
│  │Thread 2◯ │  │Thread 2◯ │  │Thread 2◯ │  │Thread 2◯ │ │
│  │          │  │          │  │          │  │          │ │
│  │Docling   │  │Docling   │  │Docling   │  │Docling   │ │
│  │Processor │  │Processor │  │Processor │  │Processor │ │
│  │          │  │          │  │          │  │          │ │
│  │PDF A     │  │PDF B     │  │PDF C     │  │PDF D     │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Processing Flow

1. **Spark Driver** starts and creates 4 worker processes
2. **Driver** discovers PDFs from the `assets/` folder
3. **PDFs are distributed** across workers (round-robin)
4. **Each worker:**
   - Imports the `docling_module` package
   - Creates a Docling processor instance
   - Processes assigned PDFs using 2 threads per PDF
   - Returns structured results (success, content, metadata, errors)
5. **Driver collects** all results into a DataFrame
6. **Results saved** as JSONL format in `output/results.jsonl/`

### Key Components

```
scripts/
├── docling_module/
│   ├── __init__.py          # Simple API: docling_process(file_path)
│   └── processor.py         # Core processor with OOP design
└── run_spark_job.py         # Main Spark orchestration script
```

## ⚙️ Configuration

### Spark Settings (Number of Workers)

Edit `scripts/run_spark_job.py` at **lines 103-112**:

```python
spark = SparkSession.builder \
    .appName("DoclingSparkJob") \
    .master("local[4]") \                     # 4 workers (change this!)
    .config("spark.executor.memory", "2g") \  # RAM per worker
    .config("spark.driver.memory", "2g") \    # Driver RAM
    .getOrCreate()
```

**Configuration Options:**

| Setting | Default | Description | Recommendation |
|---------|---------|-------------|----------------|
| `local[N]` | `local[4]` | Number of workers | Set to number of CPU cores |
| `executor.memory` | `2g` | RAM per worker | 2-4g depending on PDF size |
| `driver.memory` | `2g` | Driver RAM | 2g is usually sufficient |

**Example configurations:**

```python
# Small machine (4 cores, 8 GB RAM)
.master("local[2]") \
.config("spark.executor.memory", "2g")

# Medium machine (8 cores, 16 GB RAM) - RECOMMENDED
.master("local[4]") \
.config("spark.executor.memory", "3g")

# Large machine (16 cores, 32 GB RAM)
.master("local[8]") \
.config("spark.executor.memory", "3g")
```

### Docling Settings (Processing Options)

Edit `scripts/docling_module/processor.py` at **lines 62-84**:

```python
@dataclass
class DocumentConfig:
    # What to extract
    extract_tables: bool = True        # Extract tables
    extract_images: bool = True        # Extract images
    ocr_enabled: bool = False          # OCR for scanned PDFs
    
    # Performance settings
    num_threads: int = 2               # Threads per PDF (IMPORTANT!)
    accelerator_device: str = "cpu"    # MUST be "cpu" for Spark
    timeout_per_document: int = 300    # 5 min timeout
    
    # Enrichment (disabled for performance)
    enrich_code: bool = False
    enrich_formula: bool = False
    enrich_picture_classes: bool = False
    enrich_picture_description: bool = False
```

**Key Settings to Change:**

| Setting | Default | When to Change | Impact |
|---------|---------|----------------|--------|
| `num_threads` | 2 | **Change to 4** for speed | 30% faster processing |
| `ocr_enabled` | False | Enable for scanned PDFs | Slower but needed for images |
| `accelerator_device` | "cpu" | **Never change** | GPU causes worker crashes |
| `extract_tables` | True | Disable if no tables | Slightly faster |

### Input/Output Configuration

Edit `scripts/run_spark_job.py` :

```python
# Change input directory
assets_dir = Path(__file__).parent.parent / "assets"
pdf_path = assets_dir / "2206.01062.pdf"

# Or read from a list
with open('pdf_list.txt', 'r') as f:
    file_list = [(line.strip(),) for line in f if line.strip()]

# Output path is at line 165
output_path = Path(__file__).parent.parent / "output" / "results.jsonl"
```

## 🎯 Performance Tuning

### Current Performance

**Default Configuration:**
- Workers: 4
- Threads per worker: 2
- Total parallel threads: 8
- Speed: ~14 seconds per 19-page PDF
- Throughput: ~17 PDFs per minute

### Optimization Strategy

#### 1. **Increase Threads Per Worker** (Fastest Improvement!)

**Change:** `num_threads: int = 2` → `num_threads: int = 4`

```python
# In processor.py line 72:
num_threads: int = 4  # ⚡ Doubles parallelism per PDF
```

**Impact:**
- ✅ **~30% faster** per PDF (~10 seconds instead of 14)
- ✅ Better CPU utilization
- ✅ Minimal memory increase (threads share resources)
- ⚠️ Requires sufficient CPU cores

**Math:** 4 workers × 4 threads = **16 parallel threads**

#### 2. **Add More Workers**

**Change:** `.master("local[4]")` → `.master("local[8]")`

```python
# In run_spark_job.py line 105:
.master("local[8]")  # ⚡ Double the workers
```

**Impact:**
- ✅ 2× more PDFs processed simultaneously
- ⚠️ Requires more RAM (8 workers × 2GB = 16GB)
- ⚠️ Only helps if you have many PDFs to process

**When to use:** Large batches (100+ PDFs)

#### 3. **Optimize Memory**

```python
# Reduce memory to fit more workers
.config("spark.executor.memory", "1g")  # Instead of 2g
.master("local[8]")  # Now you can run 8 workers with 8GB RAM
```
---
### Understanding Threads vs Workers

**Workers (Processes):**
- Separate Python processes
- Complete isolation (own memory)
- Process different PDFs simultaneously
- More workers = more PDFs at once

**Threads (Per Worker):**
- Share memory within a worker
- Process pages of the same PDF in parallel
- More threads = faster single PDF processing

**Example:**
```
4 workers × 2 threads = 8 total threads
├─ Worker 1 (2 threads) → Processing PDF_A (pages 1-2, 3-4, ...)
├─ Worker 2 (2 threads) → Processing PDF_B (pages 1-2, 3-4, ...)
├─ Worker 3 (2 threads) → Processing PDF_C (pages 1-2, 3-4, ...)
└─ Worker 4 (2 threads) → Processing PDF_D (pages 1-2, 3-4, ...)
```

For more details, see: [thread_explanation.md](thread_explanation.md)

## 📊 Understanding the Output

### Output Structure

Results are saved as **JSONL** (JSON Lines) format:
```
output/results.jsonl/
├── part-00000-xxxxx.json    # Results file
├── _SUCCESS                  # Success marker
└── .part-00000-xxxxx.json.crc  # Checksum
```

### JSONL Format

Each line is a complete JSON object for one PDF:

```json
{
  "document_path": "/path/to/document.pdf",
  "success": true,
  "content": "# Document Title\n\nExtracted text content...",
  "metadata": {
    "file_name": "document.pdf",
    "file_size": "1234567",
    "file_extension": ".pdf",
    "file_path": "/path/to/document.pdf",
    "num_pages": "19",
    "confidence_score": "0.95"
  },
  "error_message": null
}
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. "Java Runtime not found"

**Error Message:**
```
Unable to locate a Java Runtime.
Please visit http://www.java.com for information on installing Java.
```

**Solution:**
```bash
# macOS
brew install openjdk@11
export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"

# Ubuntu/Debian
sudo apt-get install openjdk-11-jdk

# Verify
java -version
```

---

#### 2. "ModuleNotFoundError: No module named 'docling_module'"

**Status:** ✅ **FIXED** (auto-handled in code)

**How it's fixed:**
The code automatically packages `docling_module` as a zip file and distributes it to workers (lines 117-144 in `run_spark_job.py`).

**Verify it's working:**
Look for this in the output:
```
   Packaged: docling_module/__init__.py
   Packaged: docling_module/processor.py
   ✅ Added docling_module package to Spark workers
```

## 🏗️ Architecture Deep Dive

### Project Structure

```
Docling-Spark-Distributed-Structuring/
├── scripts/
│   ├── docling_module/           # Core processing logic
│   │   ├── __init__.py           # Simple API: docling_process()
│   │   └── processor.py          # Docling processor with OOP design
│   └── run_spark_job.py          # Main Spark orchestration
│
├── assets/                        # Sample PDFs
│   ├── 2206.01062.pdf
│   ├── 2203.01017v2.pdf
│   └── 2305.03393v1.pdf
│
├── output/                        # Processing results
│   └── results.jsonl/            # JSONL output files
│
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Component Details

#### 1. **docling_module/processor.py**

**Purpose:** Core PDF processing logic using Docling

**Key Classes:**
- `DocumentConfig`: Configuration dataclass
- `ProcessingResult`: Result container
- `DoclingPDFProcessor`: Main processor class
- `DocumentProcessorFactory`: Factory for creating processors

**Key Method:**
```python
def process(self, file_path: str) -> ProcessingResult:
    """Process a PDF and return structured result."""
    # 1. Validate file
    # 2. Convert using Docling
    # 3. Extract metadata
    # 4. Return ProcessingResult
```

---

#### 2. **docling_module/__init__.py**

**Purpose:** Simplified API for Spark workers

```python
def docling_process(file_path: str) -> ProcessingResult:
    """Simple function that workers can call."""
    processor = DocumentProcessorFactory.create_processor_with_defaults()
    return processor.process(file_path)
```

---

#### 3. **run_spark_job.py**

**Purpose:** Spark orchestration and workflow

**Key Functions:**

```python
def create_spark():
    """Create Spark session and distribute docling_module."""
    # 1. Create SparkSession
    # 2. Package docling_module as zip
    # 3. Distribute to workers via addPyFile()
    
def process_pdf_wrapper(file_path: str) -> dict:
    """Wrapper that runs on workers."""
    from docling_module.processor import docling_process
    result = docling_process(file_path)
    return result.to_dict()

def main():
    """Main workflow."""
    # 1. Create Spark
    # 2. Discover PDFs
    # 3. Create DataFrame
    # 4. Apply UDF (process_pdf_wrapper)
    # 5. Collect results
    # 6. Save as JSONL
```

---

### How Workers Get the Code

This was the trickiest part to solve! Here's how it works:

**Problem:** Workers are separate processes that don't have access to `docling_module`.

**Solution:** Package and distribute (lines 117-144):

```python
# 1. Create temporary zip file
import zipfile
with zipfile.ZipFile(zip_path, 'w') as zipf:
    # 2. Add all .py files from docling_module/
    for file in os.walk(module_path):
        if file.endswith('.py'):
            zipf.write(file_path, arcname)

# 3. Distribute to workers
spark.sparkContext.addPyFile(zip_path)
```

**Result:** Each worker gets a copy of `docling_module` and can import it!

---

### Data Flow

```
1. Input: PDF file paths
   ↓
2. Spark DataFrame: ["document_path"]
   ↓
3. Apply UDF: process_pdf_wrapper(document_path)
   ↓
4. Worker imports: from docling_module.processor import docling_process
   ↓
5. Process PDF: result = docling_process(file_path)
   ↓
6. Return dict: result.to_dict()
   ↓
7. Collect results: DataFrame with all results
   ↓
8. Save: output/results.jsonl/
```

---

**Conclusion:** 
- Increasing threads from 2→4 gives **30% speedup** with minimal memory cost
- Increasing workers helps if processing 100+ PDFs
- Sweet spot: 4 workers × 4 threads = 16 parallel threads


## 🚀 Future: Kubernetes Deployment

When you're ready to scale beyond a single machine, you can deploy this system to Kubernetes. Here's a high-level overview:

### What Would Need to Change

1. **Containerization**
   - Create a Dockerfile with Spark, Python, and dependencies
   - Build Docker image with your code
   - Push to container registry (Docker Hub, ECR, GCR)

2. **Spark Configuration**
   - Change master from `local[4]` to `k8s://https://your-k8s-api`
   - Configure Docker image for workers
   - Set up Kubernetes namespace and RBAC

3. **Storage**
   - Replace local filesystem with S3/GCS/Azure Blob
   - Configure cloud storage credentials
   - Update input/output paths

4. **Resource Management**
   - Define CPU/memory limits for pods
   - Configure auto-scaling
   - Set up monitoring and logging

### Benefits of Kubernetes

- **Scale:** Process 10,000+ PDFs across multiple nodes
- **Fault Tolerance:** Auto-restart failed workers
- **Auto-Scaling:** Dynamically add/remove workers based on load
- **Cost Optimization:** Use spot instances for batch jobs
- **Monitoring:** Integrate with Prometheus/Grafana

### Required Components

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- Container registry
- Cloud storage (S3, GCS, or Azure Blob)
- Spark Kubernetes operator (optional but recommended)

### Estimated Effort

- **Setup time:** 1-2 days for first deployment
- **Configuration:** Create Dockerfile, K8s manifests, modify Spark config
- **Testing:** Validate end-to-end workflow
- **Documentation:** Track cloud-specific settings


