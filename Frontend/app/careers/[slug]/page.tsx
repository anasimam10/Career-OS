import { redirect } from "next/navigation"

export default function CareerDetailPage({ params }: { params: { slug: string } }) {
  redirect(`/careers/${params.slug}/reality-check`)
}
