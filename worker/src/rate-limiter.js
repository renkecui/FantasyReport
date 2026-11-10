/** Limits how often one visitor can try something (e.g. logging in), counted in Workers KV. */
export class RateLimiter {
  constructor(kv, { limit = 5, windowSeconds = 900, prefix = "rate:" } = {}) {
    this.kv = kv;
    this.limit = limit;
    this.windowSeconds = Math.max(60, windowSeconds);  // KV's shortest expiry is 60 seconds
    this.prefix = prefix;
  }

  /** Count one attempt; false when the visitor is over the limit. */
  async attempt(who) {
    const key = this.prefix + who;
    const count = Number(await this.kv.get(key)) || 0;
    if (count >= this.limit) return false;
    await this.kv.put(key, String(count + 1), { expirationTtl: this.windowSeconds });
    return true;
  }

  async reset(who) {
    await this.kv.delete(this.prefix + who);
  }
}
