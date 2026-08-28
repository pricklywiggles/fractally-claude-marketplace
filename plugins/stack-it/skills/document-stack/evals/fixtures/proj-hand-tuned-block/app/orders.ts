export type Order = {
  id: string;
  customer: string;
  total: string;
};

export async function listOrders(): Promise<Order[]> {
  return [
    { id: "o-1001", customer: "Northwind", total: "$412.00" },
    { id: "o-1002", customer: "Contoso", total: "$88.50" },
  ];
}
