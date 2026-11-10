/** An in-memory stand-in for a Workers KV namespace (get / put / delete). */
export class FakeKv {
  constructor() { this.data = new Map(); this.puts = []; }
  async get(key) { return this.data.has(key) ? this.data.get(key) : null; }
  async put(key, value, options = {}) { this.data.set(key, String(value)); this.puts.push({ key, options }); }
  async delete(key) { this.data.delete(key); }
}
