# Deriva Documentation Index

**Complete guide to all Deriva documentation and resources**

---

## 📚 Documentation Files Overview

### Core Documentation

#### 1. **README.md** (50 lines)
**Purpose**: Project overview, features, installation
**Best For**: GitHub visitors, first-time setup
**Read Time**: 2-5 minutes
**Contains**:
- Project description
- Key features
- Basic installation
- Quick usage examples
- Project structure overview

**How to Access**: 
```bash
cat README.md
less README.md
```

---

#### 2. **USER_MANUAL.md** (600+ lines) ⭐ PRIMARY REFERENCE
**Purpose**: Comprehensive user manual with examples
**Best For**: In-depth learning, offline reference
**Read Time**: 30-60 minutes (or skip to sections needed)
**Contains**:
- Table of contents (searchable)
- 5-minute quick start
- Step-by-step installation
- 3 usage modes (interactive, single query, with options)
- All 11 math topics documented
- Interactive commands reference
- 50+ working examples by topic
- Advanced features guide
- 8+ troubleshooting issues with solutions
- Complete API reference
- Configuration guide
- Tips & tricks

**How to Access**:
```bash
cat USER_MANUAL.md                    # View entire file
less USER_MANUAL.md                   # Page through (recommended)
grep "vector" USER_MANUAL.md          # Search by keyword
head -100 USER_MANUAL.md              # View first section
wc -l USER_MANUAL.md                  # Count lines
```

---

#### 3. **QUICK_REFERENCE.md** (150 lines) ⭐ PRINT & KEEP
**Purpose**: One-page quick reference card
**Best For**: Quick lookup, printing, immediate reference
**Read Time**: 2-3 minutes
**Contains**:
- Installation one-liner
- All 11 topics in table format
- Syntax tips and tricks
- Example one-liners
- Troubleshooting checklist
- Common keyboard shortcuts
- File locations
- Pro tips (10 best practices)

**How to Access**:
```bash
cat QUICK_REFERENCE.md         # View
lpr QUICK_REFERENCE.md         # Print
```

**Recommended**: Print this and keep by your desk!

---

### Feature Documentation

#### 4. **EMBEDDINGS_GUIDE.md** (200 lines)
**Purpose**: Semantic embeddings and auto-detection
**Best For**: Understanding auto-topic-detection feature
**Read Time**: 10-15 minutes
**Contains**:
- Overview of semantic embeddings
- nomic-embed-text model setup
- How auto-detection works
- Confidence scoring explained
- Performance characteristics
- Troubleshooting embeddings
- Advanced customization
- Future enhancements

**How to Access**:
```bash
less EMBEDDINGS_GUIDE.md
```

---

#### 5. **HELP_SYSTEM.md** (250 lines)
**Purpose**: Help system architecture and integration
**Best For**: Understanding how help works
**Read Time**: 15-20 minutes
**Contains**:
- Help system overview
- File descriptions
- Usage examples (running `--help`, `--full-help`)
- Help content breakdown
- Tier structure (brief → full → manual)
- Example outputs
- Integration with existing system
- Testing procedures
- Future enhancements

**How to Access**:
```bash
less HELP_SYSTEM.md
grep "print_brief_help" HELP_SYSTEM.md
```

---

#### 6. **IMPLEMENTATION_SUMMARY.md** (150 lines)
**Purpose**: Feature implementation details
**Best For**: Developers, understanding new features
**Read Time**: 10-15 minutes
**Contains**:
- Files created and modified
- How semantic embeddings work
- Implementation flow
- Key features explained
- Setup instructions
- Testing examples
- Performance notes
- Backward compatibility info

**How to Access**:
```bash
less IMPLEMENTATION_SUMMARY.md
```

---

#### 7. **PROJECT_OVERVIEW.md** (250 lines) ⭐ START HERE
**Purpose**: Complete project overview and structure
**Best For**: Understanding the entire project
**Read Time**: 15-20 minutes
**Contains**:
- Project structure (directory tree)
- Core components explanation
- Documentation overview
- Help system entry points
- All 11 math topics documented
- Quick reference table
- Setup and prerequisites
- Development guide
- Performance notes
- Documentation map (what to read for what)

**How to Access**:
```bash
less PROJECT_OVERVIEW.md
```

---

### Terminal/CLI Documentation

#### 8. **`python main.py --help`** (50 lines)
**Purpose**: Quick help directly in terminal
**Best For**: Immediate assistance, learning about CLI
**Read Time**: 1-2 minutes
**Contains**:
- Banner and system info
- Quick start (3 commands)
- Command-line options (5 documented)
- Hint about `--full-help`

**How to Access**:
```bash
python main.py --help
```

---

#### 9. **`python main.py --full-help`** (200+ lines)
**Purpose**: Complete manual in terminal (with paging)
**Best For**: Terminal reference, comprehensive learning
**Read Time**: 15-30 minutes (can scroll through)
**Contains**:
- All sections from `--help`
- Plus: 50+ examples
- Topic routing explained
- Interactive commands
- Features overview
- Requirements checklist
- Setup instructions
- Configuration guide
- Advanced usage patterns
- Tips & tricks
- API reference
- Troubleshooting guide
- Footer with links

**How to Access**:
```bash
python main.py --full-help
python main.py --full-help | less    # If too long
```

---

#### 10. **Help System in Code** (`help_system.py`)
**Purpose**: Source code for all help content
**Best For**: Developers extending help system
**Read Time**: Variable
**Contains**:
- `print_brief_help()` function
- `print_full_help()` function
- 15+ specialized help functions
- Color formatting utilities
- ANSI escape codes for colors

**How to Access**:
```bash
grep "def print_" help_system.py
cat help_system.py | head -100
```

---

## 📖 Documentation Map: What to Read When

### New User (First 10 minutes)
```
1. README.md (2 min)
   ↓
2. python main.py --help (2 min)
   ↓
3. Try: python main.py "solve x^2 = 9" (1 min)
   ↓
4. Read QUICK_REFERENCE.md (5 min)
```

### Learning Mode (30 minutes)
```
1. README.md
   ↓
2. python main.py --full-help
   ↓
3. QUICK_REFERENCE.md
   ↓
4. Try 5-10 examples
```

### Complete Understanding (1-2 hours)
```
1. README.md
   ↓
2. PROJECT_OVERVIEW.md
   ↓
3. USER_MANUAL.md (read sections as needed)
   ↓
4. EMBEDDINGS_GUIDE.md
   ↓
5. Try all 11 topics
```

### Troubleshooting (5-10 minutes)
```
1. QUICK_REFERENCE.md → Troubleshooting section
   ↓
2. USER_MANUAL.md → Search problem keyword
   ↓
3. EMBEDDINGS_GUIDE.md (if embedding-related)
   ↓
4. Run: python main.py --debug "problem"
```

### Developer Mode (1-2 hours)
```
1. PROJECT_OVERVIEW.md → understand structure
   ↓
2. IMPLEMENTATION_SUMMARY.md → see changes
   ↓
3. HELP_SYSTEM.md → help architecture
   ↓
4. USER_MANUAL.md → API Reference section
   ↓
5. Explore modules/ directory
```

---

## 🎯 Quick Navigation by Topic

### Getting Started
| Need | Go To |
|------|-------|
| First setup | README.md or PROJECT_OVERVIEW.md |
| Quick start | QUICK_REFERENCE.md or `--help` |
| Installation | USER_MANUAL.md → Installation section |
| Running examples | QUICK_REFERENCE.md → One-Liner Examples |

### Using Deriva
| Need | Go To |
|------|-------|
| All topics listed | USER_MANUAL.md → Topic Routing |
| Topic examples | USER_MANUAL.md → Usage Examples |
| Syntax help | QUICK_REFERENCE.md → Syntax Tips |
| Interactive commands | USER_MANUAL.md → Interactive Mode |

### Advanced Features
| Need | Go To |
|------|-------|
| Semantic embeddings | EMBEDDINGS_GUIDE.md |
| Custom models | USER_MANUAL.md → Advanced Features |
| Debug mode | QUICK_REFERENCE.md → Debug Mode |
| Performance tuning | PROJECT_OVERVIEW.md → Performance |

### Troubleshooting
| Need | Go To |
|------|-------|
| Quick fixes | QUICK_REFERENCE.md → Troubleshooting |
| Common issues | USER_MANUAL.md → Troubleshooting section |
| Embeddings issues | EMBEDDINGS_GUIDE.md → Troubleshooting |
| Debug info | `python main.py --debug` |

### Development
| Need | Go To |
|------|-------|
| Project structure | PROJECT_OVERVIEW.md |
| Feature implementation | IMPLEMENTATION_SUMMARY.md |
| Help system | HELP_SYSTEM.md |
| Module development | USER_MANUAL.md → API Reference |

---

## 📊 Documentation by Purpose

### Learning (Progressive)
1. **README.md** ← What is Deriva?
2. **QUICK_REFERENCE.md** ← How do I use it?
3. **USER_MANUAL.md** ← Deep dive into features
4. **EMBEDDINGS_GUIDE.md** ← Advanced feature

### Reference (Lookup)
- **QUICK_REFERENCE.md** ← Same topics, condensed
- **USER_MANUAL.md** → Search, grep, navigate
- **PROJECT_OVERVIEW.md** → Architecture overview
- `python main.py --help` → CLI quick lookup

### Development
- **IMPLEMENTATION_SUMMARY.md** ← What changed?
- **HELP_SYSTEM.md** ← How does help work?
- **USER_MANUAL.md → API Reference** ← Developer API
- **Source code** ← Ultimate reference

### Troubleshooting
- **QUICK_REFERENCE.md** → Troubleshooting section
- **USER_MANUAL.md** → Troubleshooting section
- **EMBEDDINGS_GUIDE.md** → Troubleshooting section
- `python main.py --debug` → Debug output

---

## 📁 File Organization

```
deriva/
├── README.md                    ← Start here (GitHub)
├── QUICK_REFERENCE.md          ← Print this!
├── USER_MANUAL.md              ← Complete guide (copy this)
├── PROJECT_OVERVIEW.md         ← Architecture overview
├── HELP_SYSTEM.md              ← How help works
├── EMBEDDINGS_GUIDE.md         ← Auto-detection explained
├── IMPLEMENTATION_SUMMARY.md   ← What was added
│
├── main.py                      ← Run: python main.py --help
├── help_system.py              ← Help implementation
├── embeddings.py               ← Semantic embeddings
├── formatter.py                ← Math formatting
├── models.py                   ← Data structures
│
└── modules/                    ← 11 math domains
    ├── algebra.py
    ├── vector.py
    └── ... (8 more)
```

---

## 🚀 Quick Commands

### View Documentation

```bash
# Markdown files (best with 'less')
less README.md
less USER_MANUAL.md              # Recommended! Use arrow keys
less QUICK_REFERENCE.md
less PROJECT_OVERVIEW.md

# Terminal help (interactive)
python main.py --help           # Brief (50 lines)
python main.py --full-help      # Complete (200+ lines)

# Terminal help with search
python main.py --full-help | grep "vector"
python main.py --full-help | less

# Search markdown files
grep "solve" USER_MANUAL.md
grep -i "error" USER_MANUAL.md
grep -n "def " help_system.py
```

### Print Documentation

```bash
# Print for reference
lpr QUICK_REFERENCE.md          # Print quick ref
lpr USER_MANUAL.md              # Print full manual (40+ pages!)

# Create PDF
python main.py --full-help | a2ps -1 -P pdf > deriva_help.pdf
```

### Copy for Offline Use

```bash
# Copy all docs to portable device
cp *.md /media/usb/deriva_docs/

# Or just the essentials
cp README.md QUICK_REFERENCE.md USER_MANUAL.md /location/
```

---

## 📋 Documentation Checklist

✅ **User-Facing**
- ✅ README.md
- ✅ QUICK_REFERENCE.md
- ✅ USER_MANUAL.md
- ✅ `python main.py --help`
- ✅ `python main.py --full-help`

✅ **Feature Documentation**
- ✅ EMBEDDINGS_GUIDE.md
- ✅ IMPLEMENTATION_SUMMARY.md
- ✅ HELP_SYSTEM.md

✅ **Developer Documentation**
- ✅ PROJECT_OVERVIEW.md
- ✅ Source code comments
- ✅ Module examples in modules/

✅ **Advanced**
- ✅ help_system.py (source)
- ✅ API Reference in USER_MANUAL.md

---

## 💡 Tips for Using Documentation

1. **Use `less` for reading**
   ```bash
   less USER_MANUAL.md
   # Space = next page, 'b' = back, 'q' = quit, '/search' = find
   ```

2. **Search effectively**
   ```bash
   grep -i "vector" USER_MANUAL.md  # Case-insensitive search
   grep -n "error" USER_MANUAL.md   # Show line numbers
   grep -B2 -A2 "matrix" USER_MANUAL.md  # Show context
   ```

3. **Print for reference**
   ```bash
   lpr QUICK_REFERENCE.md  # Print and keep by desk
   ```

4. **Share with others**
   ```bash
   cat QUICK_REFERENCE.md | mail friend@example.com
   cp USER_MANUAL.md ~/Dropbox/
   ```

5. **Version offline** 
   ```bash
   cp *.md ~/Documents/Deriva_Docs/
   ```

---

## 🔄 Documentation Updates

When features change, update:
1. **QUICK_REFERENCE.md** ← Update first (most read)
2. **USER_MANUAL.md** ← Update main reference
3. **PROJECT_OVERVIEW.md** ← Update architecture/features
4. **IMPLEMENTATION_SUMMARY.md** ← Document changes
5. **README.md** ← Update if major change
6. **help_system.py** ← Update CLI help

---

## 📞 Getting Additional Help

| Need | Contact |
|------|---------|
| Report bug | GitHub Issues |
| Request feature | GitHub Discussions |
| Ask question | GitHub Discussions |
| Share problem | Include `--debug` output |
| Live help | Community forums (if available) |

---

## Summary

**Deriva is comprehensively documented with:**

| Doc | Lines | Time | Best For |
|-----|-------|------|----------|
| README.md | 50 | 2 min | Overview |
| QUICK_REFERENCE.md | 150 | 5 min | 📌 Print & Keep |
| USER_MANUAL.md | 600 | 30 min | 📕 Complete Guide |
| PROJECT_OVERVIEW.md | 250 | 15 min | Architecture |
| EMBEDDINGS_GUIDE.md | 200 | 10 min | Auto-detection |
| HELP_SYSTEM.md | 250 | 15 min | Help system |
| IMPLEMENTATION_SUMMARY.md | 150 | 10 min | Changes |
| `--help` | 50 | 1 min | CLI quick |
| `--full-help` | 200 | 15 min | CLI complete |

**Start with**: README.md → QUICK_REFERENCE.md → USER_MANUAL.md

**Keep handy**: QUICK_REFERENCE.md (printed)

**Bookmark**: USER_MANUAL.md (for detailed ref)

---

**Happy learning! 🚀**

*Last Updated: May 2026*
*Deriva Version 1.0*
