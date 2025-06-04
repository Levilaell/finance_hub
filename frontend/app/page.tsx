export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-center">
          Finance Management
        </h1>
      </div>
      <div className="mt-8 text-center">
        <p className="text-xl mb-4">
          Sistema de gestão financeira para PMEs brasileiras
        </p>
        <div className="flex gap-4 justify-center">
          <a
            href="/auth/login"
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Login
          </a>
          <a
            href="/auth/register"
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
          >
            Registrar
          </a>
        </div>
      </div>
    </main>
  )
}