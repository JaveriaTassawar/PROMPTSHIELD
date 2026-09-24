// Single-choice category filter as a radio group (arrow keys move between
// options). Shows how many modules each category holds.
function CategoryFilter({ categories, selected, counts, onChange }) {
  return (
    <fieldset>
      <legend className="sr-only">Filter tutorials by category</legend>
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <label
            key={category.id}
            className="cursor-pointer rounded-full border border-border bg-surface/70 px-3.5 py-1.5 text-sm text-fg-muted transition duration-150 ease-snappy hover:border-accent/40 hover:text-fg has-checked:border-accent has-checked:bg-primary/15 has-checked:text-fg has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-accent"
          >
            <input
              type="radio"
              name="learning-category"
              value={category.id}
              checked={selected === category.id}
              onChange={() => onChange(category.id)}
              className="sr-only"
            />
            {category.label}
            <span className="ml-1.5 font-mono text-xs text-fg-subtle">{counts[category.id]}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}

export default CategoryFilter
