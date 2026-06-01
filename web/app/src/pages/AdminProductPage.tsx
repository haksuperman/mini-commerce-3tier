import { useEffect, useState, type FormEvent } from 'react';
import { createProduct, listProducts, updateProduct } from '../api/products';
import { getErrorMessage } from '../api/client';
import { formatPrice } from '../lib/format';
import type { Product } from '../types/api';

interface FormState {
  name: string;
  price: string;
  stock: string;
  category: string;
  description: string;
  image_url: string;
}

const emptyForm: FormState = {
  name: '',
  price: '',
  stock: '',
  category: '',
  description: '',
  image_url: '',
};

export default function AdminProductPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const reload = async () => {
    setLoading(true);
    try {
      const data = await listProducts({ page: 1, page_size: 100 });
      setProducts(data.items);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load products'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    reload();
  }, []);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const startEdit = (p: Product) => {
    setEditingId(p.id);
    setForm({
      name: p.name,
      price: p.price,
      stock: String(p.stock),
      category: p.category ?? '',
      description: p.description ?? '',
      image_url: p.image_url ?? '',
    });
    setNotice('');
    setError('');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setNotice('');
    if (!form.name.trim() || !form.price.trim() || !form.stock.trim()) {
      setError('Name, price, and stock are required');
      return;
    }
    const payload = {
      name: form.name.trim(),
      price: form.price.trim(),
      stock: Number(form.stock),
      category: form.category.trim() || null,
      description: form.description.trim() || null,
      image_url: form.image_url.trim() || null,
    };
    setSubmitting(true);
    try {
      if (editingId) {
        await updateProduct(editingId, payload);
        setNotice(`Updated product #${editingId}`);
      } else {
        const created = await createProduct(payload);
        setNotice(`Created product #${created.id}`);
      }
      resetForm();
      await reload();
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to save product'));
    } finally {
      setSubmitting(false);
    }
  };

  const setField = (key: keyof FormState) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-gray-900">Admin · Products</h1>

      {notice && (
        <div className="mb-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{notice}</div>
      )}
      {error && (
        <div role="alert" className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card mb-8 space-y-4 p-6">
        <h2 className="font-semibold text-gray-900">
          {editingId ? `Edit product #${editingId}` : 'New product'}
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Name</label>
            <input className="input" value={form.name} onChange={setField('name')} />
          </div>
          <div>
            <label className="label">Category</label>
            <input className="input" value={form.category} onChange={setField('category')} />
          </div>
          <div>
            <label className="label">Price</label>
            <input
              className="input"
              type="number"
              step="0.01"
              min="0"
              value={form.price}
              onChange={setField('price')}
            />
          </div>
          <div>
            <label className="label">Stock</label>
            <input
              className="input"
              type="number"
              min="0"
              value={form.stock}
              onChange={setField('stock')}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="label">Image URL</label>
            <input className="input" value={form.image_url} onChange={setField('image_url')} />
          </div>
          <div className="sm:col-span-2">
            <label className="label">Description</label>
            <textarea
              className="input"
              rows={2}
              value={form.description}
              onChange={setField('description')}
            />
          </div>
        </div>
        <div className="flex gap-3">
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? 'Saving…' : editingId ? 'Update product' : 'Create product'}
          </button>
          {editingId && (
            <button type="button" className="btn-secondary" onClick={resetForm}>
              Cancel
            </button>
          )}
        </div>
      </form>

      <h2 className="mb-2 font-semibold text-gray-900">Existing products</h2>
      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-gray-500">
              <tr>
                <th className="px-4 py-2">ID</th>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Price</th>
                <th className="px-4 py-2">Stock</th>
                <th className="px-4 py-2">Active</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-b border-gray-100">
                  <td className="px-4 py-2 text-gray-500">{p.id}</td>
                  <td className="px-4 py-2 font-medium text-gray-900">{p.name}</td>
                  <td className="px-4 py-2">{formatPrice(p.price)}</td>
                  <td className="px-4 py-2">{p.stock}</td>
                  <td className="px-4 py-2">{p.is_active ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-2 text-right">
                    <button className="btn-secondary px-3 py-1" onClick={() => startEdit(p)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
