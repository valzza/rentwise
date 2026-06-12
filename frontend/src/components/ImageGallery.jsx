import { useState } from "react";

export default function ImageGallery({ images = [] }) {
  const [selected, setSelected] = useState(0);
  const [lightbox, setLightbox] = useState(false);

  if (images.length === 0) {
    return <div className="aspect-video w-full rounded-xl bg-gray-200 flex items-center justify-center text-gray-400">No images</div>;
  }

  const src = (img) => img.file_path?.startsWith("http") ? img.file_path : `/uploads/${img.file_path ?? img.file_id}`;

  return (
    <div className="flex flex-col gap-2">
      {/* Main image */}
      <div
        className="aspect-video w-full cursor-zoom-in overflow-hidden rounded-xl bg-gray-100"
        onClick={() => setLightbox(true)}
      >
        <img src={src(images[selected])} alt="" className="h-full w-full object-cover" />
      </div>

      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((img, i) => (
            <button
              key={img.id}
              onClick={() => setSelected(i)}
              className={`flex-shrink-0 h-16 w-24 overflow-hidden rounded-lg border-2 transition-colors ${i === selected ? "border-brand-500" : "border-transparent"}`}
            >
              <img src={src(img)} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90" onClick={() => setLightbox(false)}>
          <img src={src(images[selected])} alt="" className="max-h-screen max-w-screen-lg object-contain" />
          <button className="absolute right-6 top-6 text-white text-3xl" onClick={() => setLightbox(false)}>&times;</button>
        </div>
      )}
    </div>
  );
}
