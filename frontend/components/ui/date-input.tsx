"use client"

import * as React from "react"
import { CalendarIcon } from "lucide-react"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

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
  placeholder = "Pick a date",
  className,
  disabled,
}: DateInputProps) {
  const [open, setOpen] = React.useState(false)
  const [inputValue, setInputValue] = React.useState("")

  // Update input value when the value prop changes
  React.useEffect(() => {
    setInputValue(value ? format(value, "yyyy-MM-dd") : "")
  }, [value])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    
    if (newValue) {
      const date = new Date(newValue)
      if (!isNaN(date.getTime())) {
        onChange?.(date)
      }
    } else {
      onChange?.(undefined)
    }
  }

  return (
    <div className={cn("relative", className)}>
      <Input
        type="date"
        value={inputValue}
        onChange={handleInputChange}
        disabled={disabled}
        className="pr-10"
        placeholder={placeholder}
      />
      <CalendarIcon className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
    </div>
  )
}