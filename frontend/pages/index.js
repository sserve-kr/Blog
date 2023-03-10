import {
  Flex,
  useDisclosure,
  Collapse, Box, useToast,
  Text,
  Spinner, Menu, MenuButton, IconButton, MenuList, MenuItem
} from "@chakra-ui/react";
import DefaultLayout from "@/layouts/default";
import SearchBar from "@/components/searchbar";
import {useEffect, useState} from "react";
import {ViewIcon} from "@chakra-ui/icons";

import {PostItem, SeriesItem} from "@/components/items";
import {PageNavigation} from "@/components/navigation";


export default function Index() {
  let {isOpen: isSearchBarOpen, onOpen: onSearchBarOpen, onClose: onSearchBarClose} = useDisclosure();

  let [searchTags, setSearchTags] = useState([]);
  let [searchQuery, setSearchQuery] = useState("");
  let [tagIdDict, setTagIdDict] = useState({});

  let [page, setPage] = useState(1);
  let [maxPage, setMaxPage] = useState(1);

  let [posts, setPosts] = useState(undefined);
  let [series, setSeries] = useState(undefined);

  let [searchTriggered, setSearchTrigger] = useState(true);

  let [type, setType] = useState("post");

  let toast = useToast();

  useEffect(() => {
    if (!searchTriggered) return;
    setPosts(undefined);
    setSeries(undefined);
    if (type === "post") {
      fetch(`/api/post?p=${page}&${searchQuery ? "qn="+searchQuery+"&" : ""}${searchTags.map(tag => "qt="+tag).join("&")}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        }
      }).then(res => {
        if (res.status === 200) {
          return res.json();
        } else {
          toast({
            title: "Error",
            description: "An error occurred while fetching posts.",
            status: "error",
            duration: 5000,
            isClosable: false,
          })
          return null;
        }
      }).then(data => {
        if (data === null) {
          setPosts(null);
          return;
        }
        setPosts(data["posts"]);
        setMaxPage(data["max_page"]);
      })
    } else if (type === "series") {
      fetch(`/api/series?p=${page}&${searchQuery ? "qn="+searchQuery+"&" : ""}${searchTags.map(tag => "qt="+tag).join("&")}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        }
      }).then(res => {
        if (res.status === 200) {
          return res.json();
        } else {
          toast({
            title: "Error",
            description: "An error occurred while fetching series.",
            status: "error",
            duration: 5000,
            isClosable: false,
          })
          return null;
        }
      }).then(data => {
        if (data === null) {
          setSeries(null);
          return;
        }
        setSeries(data["series"]);
        setMaxPage(data["max_page"]);
      })
    }
    setSearchTrigger(false);
  }, [page, searchQuery, searchTags, searchTriggered, toast, type])

  return <DefaultLayout
    searchBarEnabled={true}
    onSearchBarOpen={onSearchBarOpen}
    onSearchBarClose={onSearchBarClose}
    extraButtons={
      <Menu>
        <MenuButton as={IconButton} icon={<ViewIcon />} />
        <MenuList>
          <MenuItem onClick={() => {setType("post");setSearchTrigger(true);}}>Post</MenuItem>
          <MenuItem onClick={() => {setType("series");setSearchTrigger(true);}}>Series</MenuItem>
        </MenuList>
      </Menu>
    }
  >
    <Flex
      direction={"column"}
      justifyContent={"flex-start"}
      alignItems={"center"}
      position={"sticky"}
      top={"navheight"}
      w={"100%"}
      zIndex={"50"}
      boxSizing={"border-box"}
      rowGap={"10px"}
      bgColor={"secondbg"}
    >
      <Collapse in={isSearchBarOpen}>
        <Box w={"100%"} pb={"10px"}>
          <SearchBar
            searchTags={searchTags}
            setSearchTags={setSearchTags}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            tagIdDict={tagIdDict}
            setTagIdDict={setTagIdDict}
            searchHandler={() => {setSearchTrigger(true)}}
          />
        </Box>
      </Collapse>
    </Flex>
    <Flex
      flexDirection={"column"}
      justifyContent="flex-start"
      alignItems="center"
      marginTop={"40px"}
      marginBottom={"40px"}
      gap={"20px"}
    >
      {
        function ItemHandler() {
          if (type === "post") {
            if (posts === undefined) {
              return <Spinner />
            }
            if (posts === null) {
              return <Text>There was unexpected error while fetching posts.<br />Please reload the page.</Text>
            }
            if (posts.length === 0) {
              return <Text>No posts found.</Text>
            }
            return posts.map(post => <PostItem key={post.id} post={post} />)
          } else if (type === "series") {
            if (series === undefined) {
              return <Spinner />
            }
            if (series === null) {
              return <Text>There was unexpected error while fetching series.<br />Please reload the page.</Text>
            }
            if (series.length === 0) {
              return <Text>No series found.</Text>
            }
            return series.map(series_obj => <SeriesItem key={series_obj.id} series={series_obj} />)
          }
        }()
      }
    </Flex>
    <PageNavigation
      page={page}
      maxPage={maxPage}
      onPageChange={(p) => {
        setPage(p);
        setSearchTrigger(true);
      }}
    />
  </DefaultLayout>
}
