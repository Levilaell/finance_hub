import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Middleware simplificado para autenticação
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token') || 
                request.headers.get('Authorization');

  // Rotas protegidas
  const protectedPaths = ['/dashboard', '/accounts', '/reports', '/settings'];
  const isProtectedPath = protectedPaths.some(path => 
    request.nextUrl.pathname.startsWith(path)
  );

  // Se é rota protegida e não tem token, redirecionar para login
  if (isProtectedPath && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Se tem token e está tentando acessar login/register, redirecionar para dashboard
  if (token && (request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/register')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
