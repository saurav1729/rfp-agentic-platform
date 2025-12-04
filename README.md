Running your FastAPI app **inside a virtual environment (venv) is the recommended way**.

# ✅ **How to create & activate a venv**

### **1️⃣ Create a virtual environment**

Run this inside your project folder:

```bash
python3 -m venv venv
```

(On Windows you may use `python` instead of `python3`)

---

### **2️⃣ Activate the venv**

#### **On Windows (PowerShell):**

```bash
venv\Scripts\Activate
```

#### **On macOS / Linux:**

```bash
source venv/bin/activate
```

When activated, your terminal will show:

```
(venv) C:\project>
```

---

# ✅ **3️⃣ Install dependencies inside venv**

```bash
pip install fastapi uvicorn
```

Or if you already have a `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

# ✅ **4️⃣ Run your FastAPI app**

```bash
uvicorn app.main:app --reload
```