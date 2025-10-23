# Decision Causality - Why You Made Each Technical Choice

**Generated:** 2025-10-13 by Ares Master Control Program
**Purpose:** Understanding the "why" behind architectural decisions

## Database Decisions

### Why SQLite for Development/POC?
**Decision:** Use SQLite instead of PostgreSQL in ASX Trading AI and Business Brain

**Reasoning Chain:**
1. **Zero Configuration**: No server setup, just file-based
2. **Embedded**: Works on Windows without external dependencies
3. **Fast Development**: Immediate iteration without deployment complexity
4. **Sufficient Performance**: Handles millions of rows for backtesting
5. **Easy Backup**: Single file = simple data portability
6. **Proven Pattern**: Works well for single-user systems

**Evidence in Code:**
```python
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'trading.db')
conn = sqlite3.connect(db_path)  # No server, no config
```

**Trade-off Accepted:** Limited concurrency (not needed for POC)
**Future Plan:** PostgreSQL for Business Brain production (multi-tenant)

**Lesson:** Start simple, scale when needed, not before

---

### Why Programmatic Schema Initialization?
**Decision:** `init_db.py` with explicit CREATE TABLE statements

**Reasoning Chain:**
1. **Version Control**: Schema changes tracked in git
2. **Documentation**: Schema is self-documenting code
3. **Reproducibility**: Anyone can rebuild database from scratch
4. **No ORM Overhead**: Direct SQL for maximum control
5. **Migration Simplicity**: Clear schema evolution path

**Evidence in Code:**
```python
def init_database(db_path):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            ticker TEXT,
            date DATE,
            ...
        )
    """)
```

**Trade-off Accepted:** Manual migrations (acceptable for POC scale)
**Alternative Rejected:** SQLAlchemy ORM (too heavy for simple tables)

---

## Architecture Decisions

### Why Modular Scraper Pattern?
**Decision:** Separate scraper per data source instead of monolithic scraper

**Reasoning Chain:**
1. **Independent Failure**: One scraper fails, others continue
2. **Easy Testing**: Test each scraper in isolation
3. **Parallel Development**: Can build new scrapers without touching old ones
4. **Rate Limiting**: Each source has different limits
5. **Maintenance**: Website changes affect only one module

**Evidence in Code:**
```python
# main.py orchestrates, each scraper is independent
from scrapers.asx_announcements import scrape_asx_announcements
from scrapers.afr_news import scrape_afr_news
# Each returns consistent dict format
```

**Trade-off Accepted:** More files to manage
**Benefit Realized:** Added ABC/SMH scrapers in v2.0 without breaking anything

**Lesson:** Modularity costs upfront but saves long-term

---

### Why Rule-Based Sentiment Over ML Model?
**Decision:** Local lexicon-based analysis instead of FinBERT or other ML models

**Reasoning Chain:**
1. **Zero Dependencies**: No API calls, no model downloads
2. **Deterministic**: Same input = same output (debugging easier)
3. **Explainable**: Can see exactly which words triggered sentiment
4. **Domain-Specific**: 300+ curated financial keywords beats generic model
5. **Fast**: No GPU, no network latency
6. **Cost**: $0 vs. API costs or GPU requirements

**Evidence in Code:**
```python
POSITIVE_WORDS = {'profit', 'earnings', 'growth', ...}  # 300+ keywords
# Manual negation handling: "not profitable" → negative
# Intensifier detection: "very strong" → weighted scoring
```

**Trade-off Accepted:** 37% accuracy vs. potential 60%+ from fine-tuned model
**Future Enhancement:** Can add FinBERT as optional enhancement (see pattern)

**Lesson:** Good-enough + explainable + free beats complex + expensive for POCs

---

### Why Hybrid AI/Rules in Business Brain?
**Decision:** Rule-based pattern detection + Claude AI enhancement

**Reasoning Chain:**
1. **Works Without API**: Rule-based catches 80% of common patterns
2. **AI for Edge Cases**: Claude finds unusual patterns rules miss
3. **Cost Efficiency**: Pay for AI only when needed
4. **Confidence Scoring**: Rules give 0.9 confidence, AI varies
5. **Graceful Degradation**: System functional even if API fails

**Evidence in Code:**
```python
def analyze_email_patterns(emails):
    # Rule-based detection
    if self._is_invoice_pattern(emails):
        workflows.append({'type': 'invoice', 'confidence': 0.9})

    # AI enhancement (optional)
    if self.client:  # Only if API key present
        ai_patterns = self._ai_discover_patterns(emails)
        workflows.extend(ai_patterns)

    return workflows
```

**Trade-off Accepted:** More complex code than pure-AI approach
**Benefit Realized:** Works immediately, improves with API key

**Lesson:** Hybrid systems combine reliability of rules with flexibility of AI

---

## Technology Stack Decisions

### Why Python for Backend?
**Decision:** Python over Node.js/Go/Java for main projects

**Reasoning Chain:**
1. **Data Science Libraries**: Pandas, NumPy, yfinance are Python-native
2. **Web Scraping**: BeautifulSoup, Requests are battle-tested
3. **AI Integration**: Anthropic SDK, OpenAI SDK have best Python support
4. **Fast Prototyping**: Minimal boilerplate, rapid iteration
5. **Personal Expertise**: Strongest language proficiency

**Evidence:** 3 of 4 projects are Python-based

**Trade-off Accepted:** Slower than Go, but not bottleneck for use case
**When to Use Alternatives:** Node.js for MCP (SDK requirement), Go for high-performance (future)

---

### Why FastAPI Over Flask/Django?
**Decision:** FastAPI for Business Brain API

**Reasoning Chain:**
1. **Async Support**: Built-in async for parallel operations
2. **Type Hints**: Pydantic models = automatic validation
3. **Auto Documentation**: OpenAPI spec generated automatically
4. **Modern**: Latest Python patterns (3.11+ features)
5. **Performance**: Faster than Flask for concurrent requests

**Evidence in Code:**
```python
@app.post("/api/discover")
async def discover_workflows(request: DiscoveryRequest):  # Type-safe
    # Async operations
    result = await workflow_engine.analyze_email_patterns()
```

**Trade-off Accepted:** Smaller ecosystem than Django
**Benefit Realized:** Clean async code, auto-generated API docs

---

### Why TypeScript for MCP Server?
**Decision:** TypeScript instead of Python for Gemini MCP

**Reasoning Chain:**
1. **SDK Requirement**: MCP SDK is TypeScript-first
2. **Type Safety**: Critical for protocol implementation
3. **Async Native**: JavaScript async model fits MCP protocol
4. **npm Ecosystem**: Better for Node.js tool integrations
5. **Learning Opportunity**: Expand beyond Python comfort zone

**Evidence:** Gemini MCP is full TypeScript implementation

**Trade-off Accepted:** Less familiar than Python
**Benefit Realized:** Successful MCP server, TypeScript proficiency gained

**Lesson:** Choose tech based on ecosystem fit, not just familiarity

---

## Feature Decisions

### Why Multi-Source Validation?
**Decision:** Add ABC News + SMH to ASX Trading AI v2.0

**Reasoning Chain:**
1. **Single Source Unreliable**: AFR misses stories, has bias
2. **Confidence Boosting**: Same news from 3 sources = high confidence
3. **Credibility Weighting**: ASX (1.0) > AFR (0.95) > ABC (0.90) > SMH (0.85)
4. **Quality Filter Need**: Discovered 26% of announcements are noise
5. **Backtesting Proof**: v1.0 had -4.63% return, needed better signals

**Evidence in Code:**
```python
# Multi-source validator
credibility_scores = {
    'ASX': 1.0,     # Official source
    'AFR': 0.95,    # Financial specialist
    'ABC': 0.90,    # General news
    'SMH': 0.85     # General news
}

# Enhanced confidence formula
confidence = 0.6 * sentiment_confidence + 0.4 * multi_source_score
```

**Trade-off Accepted:** More scrapers to maintain
**Benefit Realized:** Better signal quality (though still needs calibration)

**Lesson:** Validation requires multiple perspectives

---

### Why Quality Filtering?
**Decision:** Filter out administrative announcements in ASX Trading AI

**Reasoning Chain:**
1. **Noise Discovery**: Manual review showed ~30% low-value announcements
2. **Trading Impact**: "Appendix X" doesn't move prices
3. **Backtesting Proof**: Noise creates false signals
4. **Simple Implementation**: Keyword-based filtering sufficient
5. **Measurable Benefit**: Removed 26% noise (79 of 300 announcements)

**Evidence in Code:**
```python
def calculate_quality_score(announcement):
    low_quality_types = ['Appendix', 'Notice of Meeting', 'Change of Address']
    if any(lq in title for lq in low_quality_types):
        return 0.2  # Low quality
    return 0.9  # High quality
```

**Trade-off Accepted:** Might filter some important announcements
**Benefit Realized:** 26% reduction in noise, cleaner signals

**Lesson:** Data quality > data quantity

---

### Why Paper Trading Instead of Live?
**Decision:** Build paper trading system before live trading

**Reasoning Chain:**
1. **Risk-Free Validation**: Test strategies without capital risk
2. **Performance Tracking**: Real-time validation of backtest assumptions
3. **Confidence Building**: Prove system works before real money
4. **Regulatory Compliance**: No licensing needed for paper trading
5. **Learning**: Understand market behavior without financial consequences

**Evidence:** Complete paper trading system with live monitoring

**Trade-off Accepted:** No real profits yet
**Benefit Realized:** Discovered system needs improvement (37% sentiment accuracy)

**Lesson:** Validate with fake money before risking real money

---

## Development Workflow Decisions

### Why Comprehensive Documentation?
**Decision:** Write extensive guides, not just code comments

**Reasoning Chain:**
1. **Future Self**: Will forget implementation details in 3 months
2. **Collaboration**: Others need context to contribute
3. **Debugging**: Documented systems easier to troubleshoot
4. **Learning**: Writing forces clear thinking
5. **Professional Image**: Production-quality docs attract users/investors

**Evidence:** 27+ markdown files in ASX Trading AI

**Trade-off Accepted:** Time spent writing vs. coding
**Benefit Realized:** Can resume project after weeks away, immediately productive

**Lesson:** Documentation is code for humans

---

### Why Embedded Test Functions?
**Decision:** `if __name__ == '__main__'` tests instead of pytest

**Reasoning Chain:**
1. **Immediate Validation**: Run file directly to test
2. **Self-Documenting**: Test shows how to use the module
3. **No Framework**: Zero testing dependencies
4. **Practical**: Tests real functionality, not mocked
5. **Fast**: No test discovery, just `python file.py`

**Evidence in Code:**
```python
def test_local_analyzer():
    """Test the local sentiment analyzer."""
    analyzer = LocalSentimentAnalyzer()
    test_articles = [...]  # Real examples
    for article in test_articles:
        result = analyzer.analyze_article(...)
        print(f"Result: {result}")  # Visual verification

if __name__ == '__main__':
    test_local_analyzer()
```

**Trade-off Accepted:** No CI/CD integration (yet)
**Benefit Realized:** Instant feedback, easy debugging

**Lesson:** Practical testing beats formal testing for solo development

---

### Why Color-Coded Console Output?
**Decision:** ANSI color codes in CLI instead of plain text

**Reasoning Chain:**
1. **Visual Hierarchy**: Errors in red, success in green
2. **User Experience**: Easier to scan output
3. **Professional Feel**: Looks polished, not amateur
4. **No Dependencies**: Built-in terminal support
5. **Windows Compatibility**: Explicit Windows console mode setup

**Evidence in Code:**
```python
class Colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'

logger.info(f"{Colors.OKGREEN}✓ Success{Colors.ENDC}")
logger.error(f"{Colors.FAIL}✗ Failed{Colors.ENDC}")
```

**Trade-off Accepted:** More complex than plain text
**Benefit Realized:** Significantly better UX, faster issue identification

**Lesson:** Small UX details matter

---

## Error Handling Decisions

### Why Graceful Degradation?
**Decision:** Multiple fallback layers instead of fail-fast

**Reasoning Chain:**
1. **Partial Success**: 5 of 6 scrapers succeed = still valuable
2. **User Experience**: Show what worked, explain what failed
3. **Debugging**: Detailed error logs help fix issues
4. **Production Readiness**: Real systems handle failures gracefully
5. **Data Completeness**: Partial data > no data

**Evidence in Code:**
```python
def run_scraper(scraper_func, scraper_name, logger, *args, **kwargs):
    try:
        result = scraper_func(*args, **kwargs)
        return ScraperResult(success=True, records=count)
    except Exception as e:
        logger.error(f"Failed: {e}")
        logger.exception("Full traceback:")
        return ScraperResult(success=False, error=str(e))
    # Main continues with other scrapers
```

**Trade-off Accepted:** More complex error handling
**Benefit Realized:** System useful even with partial failures

**Lesson:** Production systems handle failure, toys crash

---

### Why Rate Limiting?
**Decision:** Built-in delays between requests

**Reasoning Chain:**
1. **Ethical Scraping**: Respect server resources
2. **Avoid Bans**: Too fast = IP block
3. **Legal Compliance**: robots.txt respect
4. **Reliability**: Reduces server errors
5. **Professional Courtesy**: Don't be a bad actor

**Evidence in Code:**
```python
ASX_RATE_LIMIT = 2  # seconds
AFR_RATE_LIMIT = 3

def rate_limit_wait(seconds):
    time.sleep(seconds)

# After each request
rate_limit_wait(ASX_RATE_LIMIT)
```

**Trade-off Accepted:** Slower scraping
**Benefit Realized:** No IP bans, stable scraping

**Lesson:** Slow and reliable beats fast and blocked

---

## Business Model Decisions

### Why B2B SaaS for Business Brain?
**Decision:** Target businesses, not consumers

**Reasoning Chain:**
1. **Higher Willingness to Pay**: Businesses buy time savings
2. **Concrete ROI**: Can calculate exact dollar value
3. **Larger Market**: Every business has repetitive workflows
4. **Retention**: Business processes are sticky
5. **Less Competition**: Consumer automation is crowded

**Evidence:** Pricing tiers in README ($99-$599/month)

**Trade-off Accepted:** Longer sales cycle than consumer
**Future Benefit:** Higher LTV, more stable revenue

---

### Why Australian Market First?
**Decision:** Deploy on Australian servers, target AU businesses

**Reasoning Chain:**
1. **Data Residency**: Australian Privacy Act compliance
2. **Local Expertise**: ASX trading knowledge
3. **Less Competition**: US market is saturated
4. **Network Effects**: Local references easier
5. **Time Zone**: Same time zone = better support

**Evidence:** Multiple AU-specific projects (ASX, AFR, SMH)

**Trade-off Accepted:** Smaller market than US
**Benefit Realized:** Domain expertise in AU financial markets

---

## Key Decision-Making Principles Extracted

1. **Start Simple, Scale When Needed**: SQLite → PostgreSQL, Rules → AI
2. **Explainable > Accurate** (for POCs): 37% accurate but explainable sentiment
3. **Partial Success > All-or-Nothing**: Graceful degradation everywhere
4. **Document for Future Self**: You'll forget, write it down
5. **Validate Before Scaling**: Paper trading before live trading
6. **Choose Tech for Ecosystem**: TypeScript for MCP, Python for data science
7. **Build Fallbacks Day 1**: AI enhancement, not dependency
8. **User Experience Matters**: Colors, help text, dry-run modes
9. **Practical > Perfect**: Embedded tests over formal test suites
10. **Business Value First**: ROI calculations, concrete metrics

---

**Meta-Insight:** Your decisions consistently prioritize **practical deployment** over theoretical perfection. You build systems that work immediately, then enhance them with sophistication. This "working foundation + incremental improvement" pattern is your core engineering philosophy.
