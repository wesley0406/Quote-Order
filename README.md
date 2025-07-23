# 📊 Automated Quote and Order Analysis Tool for ERP Systems

This project is designed to **automate and visualize the quotation and order process** by integrating data from Excel, a local database, and an ERP system. It enables both engineers and non-technical users to efficiently track costs, prices, and profit history — all through a simple web interface accessible via desktop or mobile.

---

##  I.🔧 Features of the Website

### 🧠 Cost & Quote Analysis
**Problem:** Manual cost analysis through Excel was time-consuming and error-prone. Sales often had to recalculate from scratch.
- Automates cost breakdown and profit margin tracking
- Solves traditional manual pricing and quote tracking issues

### 📥 Excel-Based Input
**Problem:** Non-technical staff couldn't easily operate Python scripts or web tools to input data.
- Supports Excel input for non-engineers to easily upload or verify data
- Printable reports allow physical verification when needed

### 🔄 Auto-Update System

**Problem:** We constantly missed files or used outdated data, which led to incorrect pricing or delayed quotes.
- Integrates with ERP and internal database using Oracle connection
- Automatically updates data daily and flags missing or outdated files

### 📈 Interactive Web Dashboard
**Problem:** Before, we had no quick way to compare current and historical quotes, making it hard to see pricing trends or detect margin changes.
- Displays real-time price and cost comparison charts
- Visual tools make it easy to analyze historical performance
- Hosted via `ngrok`, making the dashboard accessible on PC, iPad, or mobile
- Allows managers to check quotation status anytime, anywhere — solving timezone and document transmission issues

### 💼 Real-Time ERP Integration
- Quotes are matched with historical ERP records instantly
- Sales team can view last price, cost, and profit without digging into paper files or making manual calculations

---

### II. 🏷️ Automated Label Download System

**Problem:**  
Previously, we had to log into the customer portal manually to download shipping and product labels. For each order (often 50–100 labels per order), this was not only time-consuming but also prone to human error.  
A small mistake — such as entering the wrong LOT number or downloading the wrong label — could result in incorrect labeling on the product, leading to customer complaints.

**Why I built this:**  
To reduce pressure on the sales team and prevent production errors caused by incorrect labels. I wanted to automate the whole process so sales staff can focus on important tasks instead of clicking through portals.

**How it works:**  
- Uses `selenium`, to log into the customer label portal and interact with it just like a human would.
- Cross-validates the LOT numbers using **pandas** to detect duplicates and prevent manual errors.
- If the **order number format is incorrect** (e.g., user mistypes `4500037768` as `450037768`), the system automatically raises an alert and requests a manual check.
- The **Chrome WebDriver runs independently**, so once the process is started, no monitoring is needed. It downloads the correct labels and saves them to the specified folder, saving hours of manual work per week.

---
### III. 📦 Automated Volume & Weight Calculation System

**Problem:**  
For customers who order a full container load (20 ft or 40 ft), we are responsible for calculating the total volume and weight of the shipment.  
- If we **overestimate the volume**, the container ends up under-filled, leading to wasted freight cost.  
- If we **underestimate the weight**, and it exceeds the legal shipping limit, the company may be fined.  
- Manually doing these calculations for hundreds of boxes is slow and easy to mess up.

**Why I built this:**  
To avoid financial penalties, save shipping cost, and reduce manual labor, I created an automated system to simulate container loading and calculate both total volume and weight — quickly and accurately.

**How it works:**  
- Uses `cx_Oracle` to pull real order data directly from our ERP system.
- Combines package information (box type, dimensions, weight) with screw weight using `pandas`.
- Calculates stacking logic based on standard pallet constraints (e.g., **2 pallets per pillar** or **3 pallets per pillar**, depending on height).
- Simulates how goods will be arranged in a container and tracks:
  - 📦 Current estimated volume (m³)  
  - ⚖️ Total weight (kg)  
- Gives visual and numeric feedback to indicate if the load is reaching container limits — helping logistics plan efficiently and avoid misjudgment.


 


--- 
## 🛠️ Tech Stack

- **Python**: Core scripting and automation
- **pandas**: Data manipulation and transformation
- **cx_Oracle**: ERP database connection
- **Dash / Flask**: Interactive web dashboard
- **ngrok**: Remote access tunneling for web dashboard
- **Excel**: User-friendly input/output format

---

## 🚀 Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/wesley0406/Quote-Order.git
   cd Quote-Order
