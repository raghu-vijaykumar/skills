// A limit of 0 (or null/undefined) means "no limit": return every item.
export function applyLimit(items, limit) {
  return limit && limit > 0 ? items.slice(0, limit) : items;
}
