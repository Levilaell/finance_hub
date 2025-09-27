import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <div className="text-center">
        <h1 className="mb-4 text-6xl font-bold">404</h1>
        <h2 className="mb-4 text-2xl font-semibold">Página não encontrada</h2>
        <p className="mb-8 text-muted-foreground">
          A página que você está procurando não existe ou foi movida.
        </p>
        <Button asChild className="btn-primary">
          <Link href="/">
            Voltar ao início
          </Link>
        </Button>
      </div>
    </div>
  )
}