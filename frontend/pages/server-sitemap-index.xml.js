import { getServerSideSitemapIndex } from "next-sitemap";
import loc from "@/globals";

export const getServerSideProps = async (ctx) => {
  let post_ids = await fetch(loc.backend("/api/post-ids"), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    }
  })

  let series_ids = await fetch(loc.backend("/api/series-ids"), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    }
  })

  return getServerSideSitemapIndex(ctx, [
    ...(await post_ids.json()).map(id => `/post/${id}`),
    ...(await series_ids.json()).map(id => `/series/${id}`)
  ])
}

export default function SitemapIndex() {}