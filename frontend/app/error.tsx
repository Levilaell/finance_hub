'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <div className="text-center">
        <h2 className="mb-4 text-2xl font-bold">Algo deu errado!</h2>
        <p className="mb-8 text-muted-foreground">
          Ocorreu um erro ao processar sua solicitação.
        </p>
        <Button
          onClick={() => reset()}
          className="btn-primary"
        >
          Tentar novamente
        </Button>
      </div>
    </div>
  )
}