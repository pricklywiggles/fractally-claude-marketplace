import { listOrders } from "./orders";

export default async function OrdersPage() {
  const orders = await listOrders();

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-xl font-semibold">Orders</h1>
      <ul className="mt-4 divide-y">
        {orders.map((order) => (
          <li key={order.id} className="flex justify-between py-2">
            <span>{order.customer}</span>
            <span className="tabular-nums">{order.total}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
