export default function TestCSS() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">CSS Test Page</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Card 1</h2>
            <p className="text-gray-600">This is a test card with Tailwind CSS styling.</p>
            <button className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Button
            </button>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Card 2</h2>
            <p className="text-gray-600">Another test card to verify CSS is working.</p>
            <button className="mt-4 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
              Button
            </button>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Card 3</h2>
            <p className="text-gray-600">Third test card with different styling.</p>
            <button className="mt-4 bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded">
              Button
            </button>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">CSS Variables Test</h2>
          <div className="space-y-4">
            <div className="p-4 bg-primary text-primary-foreground rounded">
              Primary Color (CSS Variable)
            </div>
            <div className="p-4 bg-secondary text-secondary-foreground rounded">
              Secondary Color (CSS Variable)
            </div>
            <div className="p-4 bg-muted text-muted-foreground rounded">
              Muted Color (CSS Variable)
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}