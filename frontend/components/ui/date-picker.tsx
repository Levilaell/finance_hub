"use client"

import * as React from "react"
import { DateInput } from "@/components/ui/date-input"

interface DatePickerProps {
  date?: Date
  onDateChange?: (date: Date | undefined) => void
  placeholder?: string
  disabled?: boolean
}

export function DatePicker({ date, onDateChange, placeholder = "Pick a date", disabled }: DatePickerProps) {
  return (
    <DateInput
      value={date}
      onChange={onDateChange}
      placeholder={placeholder}
      disabled={disabled}
    />
  )
}