
import React, { useEffect, useState } from "react"
import { Streamlit, withStreamlitConnection, ComponentProps } from "streamlit-component-lib"

const DropdownComponent = (props: ComponentProps) => {
  const options = props.args["options"] as string[]
  const [filter, setFilter] = useState("")
  const [selected, setSelected] = useState("")

  useEffect(() => {
    Streamlit.setFrameHeight()
  }, [])

  useEffect(() => {
    Streamlit.setComponentValue(selected)
  }, [selected])

  const sortedOptions = [...options].sort((a, b) => {
    const re = /^(\d+)([A-Z]*)/
    const [_, na = "0", la = ""] = a.match(re) || []
    const [__, nb = "0", lb = ""] = b.match(re) || []
    return (parseInt(na) - parseInt(nb)) || la.localeCompare(lb)
  })

  const filtered = sortedOptions.filter(o => o.toLowerCase().includes(filter.toLowerCase()))

  return (
    <div style={{ fontFamily: "Segoe UI", width: "100%", maxWidth: 500 }}>
      <input
        placeholder="Otsi liini..."
        value={filter}
        onChange={e => setFilter(e.target.value)}
        style={{ width: "100%", padding: "10px", marginBottom: "10px", borderRadius: "10px", border: "1px solid #ccc", fontSize: "16px" }}
      />
      <select
        size={8}
        onChange={(e) => setSelected(e.target.value)}
        style={{ width: "100%", padding: "10px", borderRadius: "10px", border: "1px solid #ccc", fontSize: "16px" }}
      >
        {filtered.map((opt, idx) => (
          <option key={idx} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  )
}

export default withStreamlitConnection(DropdownComponent)
