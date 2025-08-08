"use client"

import * as React from "react"

interface DateInputProps {
  value?: Date
  onChange?: (date: Date | undefined) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function DateInput({
  value,
  onChange,
  placeholder = "DD/MM/AAAA",
  className,
  disabled,
}: DateInputProps) {
  const [localValue, setLocalValue] = React.useState("")

  // Update local value when prop changes
  React.useEffect(() => {
    if (value) {
      const year = value.getFullYear()
      const month = String(value.getMonth() + 1).padStart(2, '0')
      const day = String(value.getDate()).padStart(2, '0')
      setLocalValue(`${year}-${month}-${day}`)
    } else {
      setLocalValue("")
    }
  }, [value])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setLocalValue(newValue)
    
    // Only trigger onChange when we have a valid complete date
    if (newValue && /^\d{4}-\d{2}-\d{2}$/.test(newValue)) {
      const [year, month, day] = newValue.split('-').map(Number)
      if (year > 1900 && year < 2100 && month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const date = new Date(year, month - 1, day, 12, 0, 0)
        if (!isNaN(date.getTime())) {
          onChange?.(date)
        }
      }
    } else if (!newValue) {
      onChange?.(undefined)
    }
  }

  return (
    <input
      type="date"
      value={localValue}
      onChange={handleInputChange}
      disabled={disabled}
      className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className || ""}`}
      placeholder={placeholder}
    />
  )
}