# Bandwidth Optimization Guide for Residential Proxy Usage

## Current Status
- **Current bandwidth per check:** ~3.5 MB
- **Breakdown:** 115 KB sent, 3.35 MB received, 318 requests

## Cost Analysis (Residential Proxy)
If using residential proxies at typical rates:
- **Bright Data / Smartproxy:** ~$15-25/GB
- **Cost per check:** ~$0.05-0.09 per phone number
- **Cost for 100 numbers:** ~$5-9
- **Cost for 1,000 numbers:** ~$50-90

## Bandwidth Reduction Strategies

### ✅ Already Implemented
1. **Images disabled** - Saves ~40-60% bandwidth
2. **CSS/Stylesheets disabled** - Saves ~10-15%
3. **Eager page load strategy** - Don't wait for all resources
4. **URL blocking** - Block CDN, analytics, fonts

### 🎯 Alternative Solutions to Reduce Costs

#### Option 1: Use Datacenter Proxies for Initial Checks (RECOMMENDED)
**Pros:**
- 10-20x cheaper (~$1-3/GB vs $15-25/GB)
- Faster speeds
- Still works for most Facebook checks
- Only switch to residential if datacenter gets blocked

**Implementation:**
```python
# Try datacenter first, fallback to residential
proxy_types = ['datacenter', 'residential']
```

**Cost Savings:** 90-95% reduction

#### Option 2: Smart Proxy Rotation
**Strategy:**
- Use same proxy for multiple sequential checks (5-10)
- Rotate only when rate limited
- Reuse browser sessions

**Cost Savings:** 30-50% reduction

#### Option 3: Reduce Concurrent Workers
**Current:** Can use more workers
**Optimized:** Use 2-3 workers max
- Less proxy bandwidth burst
- Better rate limit management
- Slightly slower but much cheaper

#### Option 4: Mobile User-Agent + Lite Version
**Strategy:**
- Use mobile Facebook (m.facebook.com)
- Mobile version uses 50-70% less bandwidth
- Much simpler HTML/JS

**Cost Savings:** 50-70% reduction

#### Option 5: Headless Mode + Request Interception
**Strategy:**
- Run in headless mode
- Intercept and block at network layer
- Only allow essential requests

**Cost Savings:** 20-30% reduction

#### Option 6: Batch Processing with Session Reuse
**Strategy:**
- Don't close browser between checks
- Reuse same session for 10-20 checks
- Clear cookies between batches

**Cost Savings:** 40-60% reduction

## Recommended Implementation Plan

### Phase 1: Quick Wins (Implement Now)
1. ✅ Enable headless mode
2. ✅ Use mobile Facebook version
3. ✅ Reuse browser sessions

### Phase 2: Proxy Strategy (High Impact)
1. Try datacenter proxies first
2. Use residential only as fallback
3. Implement proxy rotation logic

### Phase 3: Advanced Optimization
1. Implement request-level blocking
2. Cache DNS lookups
3. Compress POST data

## Expected Results After All Optimizations
- **Target:** 200-500 KB per check (85-90% reduction)
- **New cost per check:** $0.005-0.015 (vs $0.05-0.09)
- **ROI:** 5-6x cost reduction

## Code Changes Needed
See optimized implementation in main.py with:
- Mobile version support
- Session reuse
- Datacenter proxy fallback
- Aggressive request blocking

