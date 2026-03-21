"""Tests for Story 4.1-4.4 — Topic Clusters."""
import pytest
from core.seo.topic_clusters import (
    get_cluster_for_keyword, get_cluster_links, is_pillar_keyword,
    generate_toc_html, inject_toc,
)
from core.agents.growth import _parse_cluster_map


SAMPLE_CLUSTERS = [
    {
        "name": "Ansiedade",
        "pillar_keyword": "ansiedade tratamento completo",
        "cluster_keywords": [
            "ansiedade generalizada",
            "crise de ansiedade",
            "ansiedade sintomas físicos",
            "ansiedade noturna",
        ],
    },
]

SAMPLE_INVENTORY = [
    {"keyword": "ansiedade generalizada", "url": "https://mjesus.com.br/ansiedade-generalizada"},
    {"keyword": "crise de ansiedade", "url": "https://mjesus.com.br/crise-de-ansiedade"},
    {"keyword": "depressao", "url": "https://mjesus.com.br/depressao"},
]


class TestGetClusterForKeyword:

    def test_finds_pillar(self):
        cluster = get_cluster_for_keyword("ansiedade tratamento completo", SAMPLE_CLUSTERS)
        assert cluster is not None
        assert cluster["name"] == "Ansiedade"

    def test_finds_cluster_article(self):
        cluster = get_cluster_for_keyword("ansiedade generalizada", SAMPLE_CLUSTERS)
        assert cluster is not None
        assert cluster["name"] == "Ansiedade"

    def test_not_found(self):
        assert get_cluster_for_keyword("depressao", SAMPLE_CLUSTERS) is None

    def test_case_insensitive(self):
        cluster = get_cluster_for_keyword("ANSIEDADE GENERALIZADA", SAMPLE_CLUSTERS)
        assert cluster is not None

    def test_empty_clusters(self):
        assert get_cluster_for_keyword("test", []) is None
        assert get_cluster_for_keyword("test", None) is None


class TestGetClusterLinks:

    def test_returns_links_for_cluster_article(self):
        cluster = SAMPLE_CLUSTERS[0]
        links = get_cluster_links("ansiedade noturna", cluster, SAMPLE_INVENTORY)
        assert len(links) == 2  # ansiedade generalizada + crise de ansiedade
        urls = [l["url"] for l in links]
        assert "https://mjesus.com.br/ansiedade-generalizada" in urls

    def test_no_self_link(self):
        cluster = SAMPLE_CLUSTERS[0]
        links = get_cluster_links("ansiedade generalizada", cluster, SAMPLE_INVENTORY)
        kws = [l["text"].lower() for l in links]
        assert "ansiedade generalizada" not in kws

    def test_empty_inventory(self):
        links = get_cluster_links("test", SAMPLE_CLUSTERS[0], [])
        assert links == []


class TestIsPillarKeyword:

    def test_is_pillar(self):
        assert is_pillar_keyword("ansiedade tratamento completo", SAMPLE_CLUSTERS) is True

    def test_not_pillar(self):
        assert is_pillar_keyword("ansiedade generalizada", SAMPLE_CLUSTERS) is False

    def test_empty(self):
        assert is_pillar_keyword("test", []) is False


class TestToc:

    def test_generates_toc(self):
        html = "<h1>Title</h1><h2>Intro</h2><p>text</p><h2>Causas</h2><p>text</p><h2>Tratamento</h2><p>text</p>"
        toc = generate_toc_html(html)
        assert "toc-box" in toc
        assert "Intro" in toc
        assert "Causas" in toc

    def test_no_toc_for_few_headings(self):
        html = "<h1>Title</h1><h2>Only one</h2><p>text</p>"
        assert generate_toc_html(html) == ""

    def test_inject_toc(self):
        html = "<h1>Title</h1><h2>Intro</h2><p>text</p><h2>Sec2</h2><p>text</p><h2>Sec3</h2><p>text</p>"
        result = inject_toc(html)
        assert "toc-box" in result


class TestParseClusterMap:

    def test_parses_pillar_and_cluster(self):
        lines = [
            "PILLAR: ansiedade tratamento completo",
            "CLUSTER: ansiedade generalizada sintomas",
            "CLUSTER: crise de ansiedade o que fazer",
            "CLUSTER: ansiedade noturna causas",
        ]
        result = _parse_cluster_map(lines)
        assert len(result) == 4
        assert result[0]["type"] == "pillar"
        assert result[1]["type"] == "cluster"

    def test_empty_lines_skipped(self):
        lines = ["PILLAR: test", "", "CLUSTER: sub"]
        result = _parse_cluster_map(lines)
        assert len(result) == 2

    def test_case_insensitive_prefix(self):
        lines = ["pillar: Test", "Cluster: Sub"]
        result = _parse_cluster_map(lines)
        assert len(result) == 2
