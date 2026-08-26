import { Navbar } from "@/components/navbar";
import { RestaurantSelector } from "@/components/restaurant-selector";

export default function HomePage() {
    return (
        <main className="min-h-screen bg-[#0c1011]">
            <Navbar />
            <div className="relative mx-auto max-w-7xl overflow-hidden px-5 py-14 lg:px-8 lg:py-20">
                <div className="pointer-events-none absolute left-[-10rem] top-10 h-96 w-96 rounded-full bg-[#f6a61d]/8 blur-3xl" />
                <RestaurantSelector />
            </div>
        </main>
    );
}
