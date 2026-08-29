"use client";

import { useEffect, useState } from "react";
import { fetchRestaurants, fetchRestaurantMenu, adminCreateMenuItem, adminUpdateMenuItem, adminDeleteMenuItem, adminFetchAllergens } from "@/lib/api";
import { Plus, Edit, Trash2, Save, X, Image as ImageIcon } from "lucide-react";
import { useRouter } from "next/navigation";

export default function MenuManagerPage() {
    const [restaurants, setRestaurants] = useState<any[]>([]);
    const [selectedRestaurant, setSelectedRestaurant] = useState<string>("");
    const [menuItems, setMenuItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingItem, setEditingItem] = useState<any | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [isCustomCategory, setIsCustomCategory] = useState(false);
    const [selectedImageName, setSelectedImageName] = useState<string | null>(null);
    const [masterAllergens, setMasterAllergens] = useState<any[]>([]);
    const [selectedAllergens, setSelectedAllergens] = useState<number[]>([]);
    const router = useRouter();

    const uniqueCategories = Array.from(new Set(menuItems.map(i => i.category).filter(Boolean)));

    const loadRestaurants = async () => {
        try {
            const data = await fetchRestaurants();
            setRestaurants(data);
            if (data.length > 0) {
                setSelectedRestaurant(data[0].id);
            }
        } catch(e) {
            console.error(e);
        }
    };

    const loadMenu = async (restaurantId: string) => {
        setLoading(true);
        try {
            const data = await fetchRestaurantMenu(restaurantId);
            setMenuItems(data);
        } catch(e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRestaurants();
        const loadAllergens = async () => {
            const token = localStorage.getItem("adminToken");
            if(token) {
                try {
                    const data = await adminFetchAllergens(token);
                    setMasterAllergens(data);
                } catch(e) {
                    console.error(e);
                }
            }
        };
        loadAllergens();
    }, []);

    useEffect(() => {
        if (selectedRestaurant) {
            loadMenu(selectedRestaurant);
        }
    }, [selectedRestaurant]);

    const handleDelete = async (itemId: string) => {
        if (!confirm("Are you sure you want to delete this item?")) return;
        const token = localStorage.getItem("adminToken");
        if(!token) return;
        
        try {
            await adminDeleteMenuItem(token, selectedRestaurant, itemId);
            loadMenu(selectedRestaurant);
        } catch(e: any) {
            alert(e.message);
        }
    };

    const handleSave = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const token = localStorage.getItem("adminToken");
        if(!token) return;

        const formData = new FormData(e.currentTarget);
        formData.set("is_available", (formData.get("is_available") === "on").toString());
        formData.set("direct_allergen_ids", selectedAllergens.join(","));
        
        const imageFile = formData.get("image_file") as File;
        if (!imageFile || imageFile.size === 0) {
            formData.delete("image_file");
        }

        try {
            if (isCreating) {
                await adminCreateMenuItem(token, selectedRestaurant, formData);
            } else if (editingItem) {
                await adminUpdateMenuItem(token, selectedRestaurant, editingItem.id, formData);
            }
            setEditingItem(null);
            setIsCreating(false);
            setSelectedImageName(null);
            loadMenu(selectedRestaurant);
        } catch(e: any) {
            alert(e.message);
        }
    };

    return (
        <div className="p-8 text-white max-w-6xl mx-auto w-full">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-black text-[#f6a61d]">Menu Manager</h1>
                <div className="flex gap-4 items-center">
                    <select 
                        value={selectedRestaurant} 
                        onChange={(e) => setSelectedRestaurant(e.target.value)}
                        className="bg-[#0c1011] border border-white/20 rounded-lg px-4 py-2"
                    >
                        {restaurants.map((r: any) => (
                            <option key={r.id} value={r.id}>{r.name}</option>
                        ))}
                    </select>
                    <button 
                        onClick={() => {
                            setIsCreating(true);
                            setEditingItem(null);
                            setSelectedAllergens([]);
                        }}
                        className="flex items-center gap-2 bg-[#f6a61d] text-[#0c1011] px-4 py-2 rounded-lg font-bold"
                    >
                        <Plus className="w-4 h-4" /> Add Item
                    </button>
                </div>
            </div>

            {(editingItem || isCreating) && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-[#121617] border border-white/10 rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold">{isCreating ? "New Menu Item" : "Edit Menu Item"}</h2>
                            <button onClick={() => { setEditingItem(null); setIsCreating(false); setSelectedImageName(null); setSelectedAllergens([]); }}>
                                <X className="w-5 h-5 text-zinc-400 hover:text-white" />
                            </button>
                        </div>
                        <form onSubmit={handleSave} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm mb-1 text-zinc-400">Name</label>
                                    <input required name="name" defaultValue={editingItem?.name} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2" />
                                </div>
                                <div>
                                    <label className="block text-sm mb-1 text-zinc-400">Category</label>
                                    {!isCustomCategory ? (
                                        <div className="flex gap-2">
                                            <select 
                                                name="category" 
                                                defaultValue={editingItem?.category || uniqueCategories[0] || ""} 
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white [&>option]:bg-zinc-800"
                                            >
                                                {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
                                            </select>
                                            <button 
                                                type="button" 
                                                onClick={() => setIsCustomCategory(true)}
                                                className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg shrink-0"
                                                title="Add new category"
                                            >
                                                <Plus className="w-5 h-5 text-zinc-400" />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex gap-2">
                                            <input 
                                                required 
                                                name="category" 
                                                placeholder="New category name"
                                                defaultValue={editingItem?.category} 
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2" 
                                            />
                                            {uniqueCategories.length > 0 && (
                                                <button 
                                                    type="button" 
                                                    onClick={() => setIsCustomCategory(false)}
                                                    className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg shrink-0"
                                                    title="Select existing category"
                                                >
                                                    <X className="w-5 h-5 text-zinc-400" />
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-sm mb-1 text-zinc-400">Description</label>
                                    <textarea name="description" defaultValue={editingItem?.description} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 h-20" />
                                </div>
                                <div>
                                    <label className="block text-sm mb-1 text-zinc-400">Price (₹)</label>
                                    <input required type="number" step="0.01" name="price" defaultValue={editingItem?.price} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2" />
                                </div>
                                <div>
                                    <label className="block text-sm mb-1 text-zinc-400">Spice Level</label>
                                    <select name="spice_level" defaultValue={editingItem?.spice_level || "None"} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white [&>option]:bg-zinc-800">
                                        <option value="None">None</option>
                                        <option value="Low">Low</option>
                                        <option value="Medium">Medium</option>
                                        <option value="High">High</option>
                                        <option value="Extreme">Extreme</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm mb-1 text-zinc-400">Serving Size</label>
                                    <input required type="number" name="serving_size" defaultValue={editingItem?.serving_size || 1} className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2" />
                                </div>
                                <div>
                                    <label className="block text-sm mb-1 text-zinc-400">Image</label>
                                    <div className="relative">
                                        <input 
                                            type="file" 
                                            name="image_file" 
                                            accept="image/*" 
                                            onChange={(e) => {
                                                if (e.target.files && e.target.files.length > 0) {
                                                    setSelectedImageName(e.target.files[0].name);
                                                } else {
                                                    setSelectedImageName(null);
                                                }
                                            }}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                                        />
                                        <div className={`w-full border hover:bg-white/10 transition rounded-lg px-4 py-2 flex items-center justify-center gap-2 text-sm font-medium ${selectedImageName ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-white/5 border-white/10 text-zinc-300'}`}>
                                            <ImageIcon className="w-4 h-4 shrink-0" />
                                            <span className="truncate max-w-[150px]">
                                                {selectedImageName ? selectedImageName : "Select Image File"}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-sm mb-2 text-zinc-400">Listed Allergens</label>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 bg-white/5 border border-white/10 rounded-lg p-3">
                                        {masterAllergens.map(allergen => {
                                            const isDirectlyTagged = selectedAllergens.includes(allergen.id);
                                            const isInferred = editingItem && editingItem.allergens.includes(allergen.name) && !isDirectlyTagged;
                                            
                                            return (
                                                <div key={allergen.id} className="flex flex-col">
                                                    <label className={`flex items-center gap-2 ${isInferred ? 'cursor-not-allowed text-zinc-500' : 'cursor-pointer hover:text-white text-zinc-300'} text-sm`}>
                                                        <input 
                                                            type="checkbox" 
                                                            className={`rounded border-white/20 ${isInferred ? 'bg-zinc-700' : 'bg-black/20'}`}
                                                            checked={isDirectlyTagged || isInferred}
                                                            disabled={isInferred}
                                                            onChange={(e) => {
                                                                if (e.target.checked) {
                                                                    setSelectedAllergens(prev => [...prev, allergen.id]);
                                                                } else {
                                                                    setSelectedAllergens(prev => prev.filter(id => id !== allergen.id));
                                                                }
                                                            }}
                                                        />
                                                        {allergen.name}
                                                    </label>
                                                    {isInferred && <span className="text-[10px] text-zinc-500 ml-5 leading-tight">(Inferred from ingredients)</span>}
                                                </div>
                                            );
                                        })}
                                        {masterAllergens.length === 0 && (
                                            <div className="col-span-full text-zinc-500 text-sm py-2">Loading allergens...</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-col gap-3 mt-4">
                                <div className="p-3 rounded-lg border border-white/5 bg-white/[0.02]">
                                    <div className="font-semibold text-sm mb-2">Dietary Preference</div>
                                    <select name="dietary_preference" defaultValue={editingItem ? editingItem.dietary_preference : "Non-Vegetarian"} className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-white text-sm focus:outline-none">
                                        <option value="Vegetarian">Vegetarian</option>
                                        <option value="Vegan">Vegan</option>
                                        <option value="Non-Vegetarian">Non-Vegetarian</option>
                                    </select>
                                </div>
                                <label className="flex items-start gap-3 p-3 rounded-lg border border-white/5 bg-white/[0.02] cursor-pointer hover:bg-white/[0.04] transition">
                                    <input type="checkbox" name="is_available" defaultChecked={editingItem ? editingItem.is_available : true} className="mt-1 rounded bg-white/5 border-white/10" />
                                    <div>
                                        <div className="font-semibold text-sm">Available (In Stock)</div>
                                        <div className="text-xs text-zinc-500">Uncheck to mark this dish as out of stock. It will be greyed out on the menu.</div>
                                    </div>
                                </label>
                            </div>
                            <div className="flex justify-end gap-3 pt-4 border-t border-white/10 mt-6">
                                <button type="button" onClick={() => { setEditingItem(null); setIsCreating(false); setSelectedImageName(null); }} className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10">Cancel</button>
                                <button type="submit" className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#f6a61d] text-[#0c1011] font-bold">
                                    <Save className="w-4 h-4" /> Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {loading ? (
                <div className="text-zinc-500">Loading menu...</div>
            ) : (
                <div className="grid gap-4">
                    {menuItems.map((item: any) => (
                        <div key={item.id} className="flex justify-between items-center bg-white/[0.02] border border-white/5 rounded-xl p-4 hover:bg-white/[0.04]">
                            <div className="flex items-center gap-4">
                                {item.image_url ? (
                                    <img src={item.image_url} alt={item.name} className="w-16 h-16 rounded-lg object-cover" />
                                ) : (
                                    <div className="w-16 h-16 rounded-lg bg-white/5 flex items-center justify-center">
                                        <ImageIcon className="w-6 h-6 text-white/20" />
                                    </div>
                                )}
                                <div>
                                    <h3 className="font-bold text-lg">{item.name}</h3>
                                    <p className="text-sm text-zinc-400">{item.category} • ₹{item.price}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => { setEditingItem(item); setSelectedAllergens(item.direct_allergen_ids || []); }} className="p-2 rounded-lg bg-white/5 text-blue-400 hover:bg-white/10">
                                    <Edit className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleDelete(item.id)} className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// force reload
