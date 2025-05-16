export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString(); // Customize as needed
};

export const formatPrice = (price: number): string => {
  return `$${price.toFixed(2)}`;
}; 