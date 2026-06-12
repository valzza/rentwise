import { Link } from "react-router-dom";

export default function NotFound() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
            <h1 className="text-6xl font-bold text-gray-200">404</h1>
            <p className="text-xl font-semibold text-gray-700">Page not found</p>
            <Link to="/" className="rounded-lg bg-primary-600 px-6 py-2 text-sm font-medium text-white hover:bg-primary-700">
                Go home
            </Link>
        </div>
    );
}
