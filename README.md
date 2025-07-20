# 🚣‍♂️ River Runner

> **A comprehensive desktop application for whitewater enthusiasts to catalog rivers, track paddling trips, and organize their adventures.**

Built with PyQt6, featuring beautiful nature-inspired and dark themes with intuitive two-column forms for efficient data entry.

## 🌊 Key Features

### 📊 **River Database**
- Store detailed information including difficulty class, flow rates, access points, hazards, and GPS coordinates
- Smart search & filtering by name, location, difficulty, or custom tags
- Tagging system for categorization (scenic, technical, family-friendly, etc.)
- Color-coded difficulty display (green for Class I-II, orange for Class III, red for Class IV-VI)

### 📝 **Trip Logging**
- Record paddling sessions with companions, conditions, duration, and personal ratings
- Edit and delete trip logs with full CRUD functionality
- Track your paddling progression over time

### 📎 **File Management**
- Attach photos, maps, and documents to river entries
- Clean file display with hover tooltips for technical details
- Organized file storage with timestamp management

### 📈 **Analytics & Import/Export**
- Statistics dashboard tracking paddling hours and difficulty progression
- Real-time updates when data changes
- Export and import your database to JSON for backup, sharing, or transferring between devices
- Smart duplicate detection prevents importing the same rivers or trips twice

## 🚀 Installation

### Prerequisites
```bash
pip install PyQt6 Pillow reportlab folium
```

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/jackworthen/river-run.git
   cd river-run
   ```

2. **Run the application:**
   ```bash
   python riverrun.py
   ```

3. **Start logging your adventures!** 🎉

## 💻 System Requirements

- **Python:** 3.8 or higher
- **Operating System:** Windows, macOS, or Linux
- **Memory:** 512MB RAM minimum
- **Storage:** 50MB available space

## 🎯 Perfect For

- 🛶 **Kayakers** tracking their favorite runs
- 🚣 **Canoeists** documenting scenic routes  
- 🌊 **Rafters** organizing group adventures
- 🏕️ **Outdoor enthusiasts** planning future trips

## 📱 Interface Highlights

- **🌿 Beautiful themes** - Choose between vibrant nature-inspired colors or sleek dark mode
- **⚙️ Persistent settings** - Your theme preference saves between sessions
- **📋 Two-column forms** - Efficient data entry with red asterisks for required fields
- **🔍 Smart filtering** - Find rivers quickly by any criteria
- **💾 Auto-save functionality** - Never lose your data
- **📊 Dynamic displays** - River details only show fields with actual data
- **📊 Real-time statistics** - See your progress at a glance

## 🛠️ Technical Details

- **Framework:** PyQt6 for cross-platform GUI
- **Database:** SQLite for reliable local storage
- **Architecture:** Clean MVC pattern with modular design
- **File Handling:** Automatic organization and timestamp management

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Star ⭐ this repo if you find it helpful!*

---

Developed by Jack Worthen[jackworthen](https://github.com/jackworthen)
