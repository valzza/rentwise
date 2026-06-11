import { useState } from "react";
import { mlApi } from "../api/mlApi";

export function usePriceEstimate() {
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchEstimate = async (features) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await mlApi.estimatePrice(features);
      setEstimate(data);
    } catch (err) {
      setError(err.response?.data?.detail ?? "Could not fetch price estimate");
    } finally {
      setLoading(false);
    }
  };

  return { estimate, loading, error, fetchEstimate };
}
