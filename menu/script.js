/* ═══════════════════════════════════════════════════════════════════════════
   LA ROMA - RESTAURANT MENU JAVASCRIPT
   نظام منيو المطعم الرقمي
   ═══════════════════════════════════════════════════════════════════════════

   لإضافة أطباق جديدة، قم بتعديل كائن menuData في الأسفل.
   كل تصنيف يحتوي على مصفوفة من الأطباق.
   ═══════════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════════
   1. MENU DATA - بيانات القائمة
   ═══════════════════════════════════════════════════════════════════════════
   
   لإضافة طبق جديد:
   1. حدد التصنيف المناسب (appetizers, salads, mains, drinks, desserts)
   2. أضف كائن جديد يحتوي على:
      - id: رقم فريد
      - name: اسم الطبق
      - description: وصف الطبق
      - price: السعر بالريال
      - image: رابط الصورة
      - badge: شارة (اختياري)
   
   ═══════════════════════════════════════════════════════════════════════════ */
const menuData = {
    // ═══ المقبلات ═══
    appetizers: [
        {
            id: 1,
            name: "بروتة بالروبيان",
            description: "روبيان طازج ملفوف بطبقات البانكو مقرمش مع صوص الألفريدو الكريمي",
            price: 45,
            image: "https://images.unsplash.com/photo-1625944525533-473f1a3d54e7?w=400&h=300&fit=crop",
            badge: "الأكثر طلباً"
        },
        {
            id: 2,
            name: "كروكيت بحري",
            description: "كروكيت ذهبية مقرمشة محشوة بسمك التونة الطازج مع البانكو",
            price: 38,
            image: "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400&h=300&fit=crop"
        },
        {
            id: 3,
            name: "أصابع موزاريلا",
            description: "أصابع جبنة موزاريلا مقلية مع صوص مارينارا الأصلي",
            price: 32,
            image: "https://images.unsplash.com/photo-1531749668029-2db88e4276c7?w=400&h=300&fit=crop"
        },
        {
            id: 4,
            name: "حمص ترافل",
            description: "حمص كريمي مع زيت الزيتون البكر وشرائح الكمأة الفاخرة",
            price: 28,
            image: "https://images.unsplash.com/photo-1577805947697-89e18249d767?w=400&h=300&fit=crop",
            badge: "جديد"
        },
        {
            id: 5,
            name: "ساندويتش مشروم",
            description: "فطر بورتوبيلو محشو بالخضار المشوية والجبن الذائب",
            price: 35,
            image: "https://images.unsplash.com/photo-1604152135912-04a022e23696?w=400&h=300&fit=crop"
        }
    ],

    // ═══ السلطات ═══
    salads: [
        {
            id: 6,
            name: "سلطة روما",
            description: "خس روماني طازج مع صلصة السيزر الكلاسيكية ورقائق البارميزان",
            price: 32,
            image: "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=300&fit=crop"
        },
        {
            id: 7,
            name: "سلطة الكاباتا",
            description: "طماطم طازجة مع الخيار والزيتون والفلفل الملون بصوص البيستو",
            price: 30,
            image: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop"
        },
        {
            id: 8,
            name: "سلطة السبانخ",
            description: "سبانخ طازجة مع التوت البري واللوز وجبن الشيز الكريمي",
            price: 35,
            image: "https://images.unsplash.com/photo-1600259800661-d3a010f4d8db?w=400&h=300&fit=crop",
            badge: "صحي"
        },
        {
            id: 9,
            name: "سلطة نيسواز",
            description: "خضار مشكلة مع صدور الدجاج المشوي والأفوكادو والبيض المسلوق",
            price: 42,
            image: "https://images.unsplash.com/photo-1505253716362-afaea1d3d1af?w=400&h=300&fit=crop"
        }
    ],

    // ═══ الوجبات الرئيسية ═══
    mains: [
        {
            id: 10,
            name: "فيليه لحم بقوق",
            description: "فيليه لحم بقوق مشوي مع صوص الفطر الكريمي والبطاطس المقرمشة",
            price: 145,
            image: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=300&fit=crop",
            badge: "علامة مميزة"
        },
        {
            id: 11,
            name: "سلمون مشوي",
            description: "سلمون طازج مشوي مع الليمون والأعشاب والبطاطس المهروسة",
            price: 125,
            image: "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400&h=300&fit=crop"
        },
        {
            id: 12,
            name: "سباغيتي كاربنارا",
            description: "معكرونة سباغيتي أصلية مع البيض وجبن البارميزان ولحم الخنزير المقدد",
            price: 65,
            image: "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400&h=300&fit=crop",
            badge: "الأكثر طلباً"
        },
        {
            id: 13,
            name: "لازانيا لحم",
            description: "طبق لازانيا تقليدي مع صوص اللحم المفروم وجبن الموزاريلا",
            price: 72,
            image: "https://images.unsplash.com/photo-1574894709920-11b28e7367e3?w=400&h=300&fit=crop"
        },
        {
            id: 14,
            name: "ريزوتو الفطر",
            description: "أرز أربوريو مع مزيج من الفطر المتنوع وجبن البارميزان",
            price: 68,
            image: "https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=400&h=300&fit=crop",
            badge: "نباتي"
        },
        {
            id: 15,
            name: "دجاج بارميزان",
            description: "صدر دجاج مقرمش مع صوص مارينارا وجبن الموزاريلا الذائب",
            price: 78,
            image: "https://images.unsplash.com/photo-1632778149955-e80f8ceca2e8?w=400&h=300&fit=crop"
        },
        {
            id: 16,
            name: "كوردون بلو",
            description: "دجاج محشو بالهام ولحم الخنزير المقدد مع صوص البيستو",
            price: 85,
            image: "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400&h=300&fit=crop"
        },
        {
            id: 17,
            name: "باستا بولونيز",
            description: "معكرونة بيني مع صوص اللحم الإيطالي التقليدي",
            price: 58,
            image: "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400&h=300&fit=crop"
        }
    ],

    // ═══ المشروبات ═══
    drinks: [
        {
            id: 18,
            name: "عصير ليمون",
            description: "عصير ليمون طازج محضر منزلياً مع النعناع والزنجبيل",
            price: 15,
            image: "https://images.unsplash.com/photo-1621263764928-df1444c5e859?w=400&h=300&fit=crop"
        },
        {
            id: 19,
            name: "موكتيل فراولة",
            description: "مشروب منعش مع الفراولة الطازجة واللبن والثلج",
            price: 22,
            image: "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=400&h=300&fit=crop"
        },
        {
            id: 20,
            name: "قهوة إسبريسو",
            description: "قهوة إسبريسو إيطالية أصلية محضرة بأحدث ماكينات الضغط",
            price: 12,
            image: "https://images.unsplash.com/photo-1510707577719-ae7c14805e3a?w=400&h=300&fit=crop"
        },
        {
            id: 21,
            name: "كابتشينو",
            description: "قهوة كابتشينو إيطالية مع رغوة الحليب المخفوقة",
            price: 15,
            image: "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400&h=300&fit=crop"
        },
        {
            id: 22,
            name: "شاي أخضر",
            description: "شاي أخضر ياباني طازج مع فوائد صحية متعددة",
            price: 10,
            image: "https://images.unsplash.com/photo-1556881286-fc6915169721?w=400&h=300&fit=crop"
        }
    ],

    // ═══ الحلويات ═══
    desserts: [
        {
            id: 23,
            name: "تيراميسو",
            description: "حلى تيراميسو إيطالي أصيل مع الكريما والقهوة",
            price: 35,
            image: "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400&h=300&fit=crop",
            badge: "الأكثر طلباً"
        },
        {
            id: 24,
            name: "باناكوتا",
            description: "حلى باناكوتا إيطالية مع صوص التوت الطازج",
            price: 32,
            image: "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&h=300&fit=crop"
        },
        {
            id: 25,
            name: "تشيز كيك",
            description: "تشيز كيك نيويورك الكريمي مع طبقة التوت البري",
            price: 38,
            image: "https://images.unsplash.com/photo-1524351199678-941a58a3df50?w=400&h=300&fit=crop"
        },
        {
            id: 26,
            name: "جيلاتو",
            description: "آيس كريم إيطالي طبيعي بنكهات متنوعة",
            price: 28,
            image: "https://images.unsplash.com/photo-1557142046-c704a3adf364?w=400&h=300&fit=crop",
            badge: "صنع طازج"
        },
        {
            id: 27,
            name: "براونيز",
            description: "كيك براونيز شوكولاتة غني مع آيس كريم الفانيلا",
            price: 30,
            image: "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400&h=300&fit=crop"
        }
    ]
};

/* ═══════════════════════════════════════════════════════════════════════════
   2. APPLICATION STATE - حالة التطبيق
   ═══════════════════════════════════════════════════════════════════════════ */
const state = {
    cart: [],           // عناصر السلة
    currentCategory: 'all',  // التصنيف الحالي
    searchQuery: '',    // كلمة البحث
    isDarkMode: false,  // الوضع الليلي
    taxRate: 0.15       // نسبة الضريبة 15%
};

/* ═══════════════════════════════════════════════════════════════════════════
   3. DOM ELEMENTS - عناصر الصفحة
   ═══════════════════════════════════════════════════════════════════════════ */
const elements = {
    // الهيدر
    themeToggle: document.getElementById('themeToggle'),
    floatingCart: document.getElementById('floatingCart'),
    cartBadge: document.getElementById('cartBadge'),
    
    // القائمة
    menuGrid: document.getElementById('menuGrid'),
    categoryTitle: document.getElementById('categoryTitle'),
    categoryCount: document.getElementById('categoryCount'),
    searchInput: document.getElementById('searchInput'),
    searchClear: document.getElementById('searchClear'),
    noResults: document.getElementById('noResults'),
    
    // السلة
    cartSidebar: document.getElementById('cartSidebar'),
    cartOverlay: document.getElementById('cartOverlay'),
    cartClose: document.getElementById('cartClose'),
    cartItems: document.getElementById('cartItems'),
    cartEmpty: document.getElementById('cartEmpty'),
    cartFooter: document.getElementById('cartFooter'),
    subtotal: document.getElementById('subtotal'),
    tax: document.getElementById('tax'),
    total: document.getElementById('total'),
    checkoutBtn: document.getElementById('checkoutBtn'),
    clearCartBtn: document.getElementById('clearCartBtn'),
    
    // الإشعارات
    notification: document.getElementById('notification'),
    notificationText: document.getElementById('notificationText'),
    
    // QR Code
    qrContainer: document.getElementById('qrContainer')
};

/* ═══════════════════════════════════════════════════════════════════════════
   4. INITIALIZATION - تهيئة التطبيق
   ═══════════════════════════════════════════════════════════════════════════ */
function init() {
    // تحميل السلة من التخزين المحلي
    loadCartFromStorage();
    
    // تحميل الوضع الليلي من التخزين المحلي
    loadThemeFromStorage();
    
    // عرض القائمة
    renderMenu();
    
    // إنشاء QR Code
    generateQRCode();
    
    // تهيئة الأحداث
    initEventListeners();
}

/* ═══════════════════════════════════════════════════════════════════════════
   5. MENU RENDERING - عرض القائمة
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * الحصول على جميع الأطباق من جميع التصنيفات
 */
function getAllDishes() {
    return Object.values(menuData).flat();
}

/**
 * تصفية الأطباق حسب التصنيف والبحث
 */
function getFilteredDishes() {
    let dishes = getAllDishes();
    
    // فلترة حسب التصنيف
    if (state.currentCategory !== 'all') {
        dishes = dishes.filter(dish => dish.category === state.currentCategory);
    }
    
    // فلترة حسب البحث
    if (state.searchQuery.trim()) {
        const query = state.searchQuery.toLowerCase().trim();
        dishes = dishes.filter(dish => 
            dish.name.toLowerCase().includes(query) ||
            dish.description.toLowerCase().includes(query)
        );
    }
    
    return dishes;
}

/**
 * عرض قائمة الطعام
 */
function renderMenu() {
    const dishes = getFilteredDishes();
    const totalCount = state.currentCategory === 'all' 
        ? getAllDishes().length 
        : menuData[state.currentCategory].length;
    
    // تحديث عنوان التصنيف
    elements.categoryTitle.textContent = getCategoryTitle(state.currentCategory);
    elements.categoryCount.textContent = `${totalCount} صنف`;
    
    // إظهار/إخفاء رسالة عدم وجود نتائج
    if (dishes.length === 0) {
        elements.menuGrid.innerHTML = '';
        elements.noResults.style.display = 'block';
        return;
    }
    
    elements.noResults.style.display = 'none';
    
    // عرض الأطباق
    elements.menuGrid.innerHTML = dishes.map((dish, index) => `
        <article class="menu-card" style="animation-delay: ${index * 0.05}s">
            <div class="menu-card-image">
                <img src="${dish.image}" alt="${dish.name}" loading="lazy">
                ${dish.badge ? `<span class="menu-card-badge">${dish.badge}</span>` : ''}
            </div>
            <div class="menu-card-content">
                <h3 class="menu-card-title">${dish.name}</h3>
                <p class="menu-card-desc">${dish.description}</p>
                <div class="menu-card-footer">
                    <span class="menu-card-price">${dish.price.toLocaleString()} <span>ر.س</span></span>
                    <button class="add-btn" onclick="addToCart(${dish.id})">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                        <span>إضافة</span>
                    </button>
                </div>
            </div>
        </article>
    `).join('');
}

/**
 * الحصول على عنوان التصنيف
 */
function getCategoryTitle(category) {
    const titles = {
        all: 'جميع الأطباق',
        appetizers: 'المقبلات',
        salads: 'السلطات',
        mains: 'الوجبات الرئيسية',
        drinks: 'المشروبات',
        desserts: 'الحلويات'
    };
    return titles[category] || category;
}

/* ═══════════════════════════════════════════════════════════════════════════
   6. SEARCH FUNCTIONALITY - وظيفة البحث
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * البحث في القائمة
 */
function handleSearch(query) {
    state.searchQuery = query;
    
    // إظهار/إخفاء زر المسح
    elements.searchClear.style.display = query ? 'flex' : 'none';
    
    // إعادة عرض القائمة
    renderMenu();
}

/**
 * مسح البحث
 */
function clearSearch() {
    elements.searchInput.value = '';
    handleSearch('');
}

/* ═══════════════════════════════════════════════════════════════════════════
   7. CATEGORY FILTERING - فلترة التصنيفات
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * فلترة حسب التصنيف
 */
function filterByCategory(category) {
    state.currentCategory = category;
    
    // تحديث الأزرار النشطة
    document.querySelectorAll('.main-cat-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mainCategory === category);
    });
    
    // مسح البحث
    if (state.searchQuery) {
        elements.searchInput.value = '';
        state.searchQuery = '';
        elements.searchClear.style.display = 'none';
    }
    
    // إعادة عرض القائمة
    renderMenu();
}

/* ═══════════════════════════════════════════════════════════════════════════
   8. SHOPPING CART - سلة المشتريات
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * إضافة منتج للسلة
 */
function addToCart(dishId) {
    const dish = getAllDishes().find(d => d.id === dishId);
    if (!dish) return;
    
    const existingItem = state.cart.find(item => item.id === dishId);
    
    if (existingItem) {
        existingItem.quantity++;
    } else {
        state.cart.push({
            id: dish.id,
            name: dish.name,
            price: dish.price,
            image: dish.image,
            quantity: 1
        });
    }
    
    // حفظ السلة
    saveCartToStorage();
    
    // تحديث الواجهة
    updateCartUI();
    
    // إظهار الإشعار
    showNotification(`تمت إضافة "${dish.name}"`);
}

/**
 * تحديث كمية المنتج
 */
function updateQuantity(dishId, change) {
    const item = state.cart.find(i => i.id === dishId);
    if (!item) return;
    
    item.quantity += change;
    
    if (item.quantity <= 0) {
        removeFromCart(dishId);
        return;
    }
    
    saveCartToStorage();
    updateCartUI();
}

/**
 * حذف منتج من السلة
 */
function removeFromCart(dishId) {
    const item = state.cart.find(i => i.id === dishId);
    if (!item) return;
    
    state.cart = state.cart.filter(i => i.id !== dishId);
    
    saveCartToStorage();
    updateCartUI();
    
    showNotification(`تم حذف "${item.name}"`);
}

/**
 * إفراغ السلة
 */
function clearCart() {
    if (state.cart.length === 0) return;
    
    if (confirm('هل أنت متأكد من إفراغ السلة؟')) {
        state.cart = [];
        saveCartToStorage();
        updateCartUI();
        showNotification('تم إفراغ السلة');
    }
}

/**
 * حساب المجموع
 */
function calculateTotals() {
    const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const tax = subtotal * state.taxRate;
    const total = subtotal + tax;
    
    return { subtotal, tax, total };
}

/**
 * تحديث واجهة السلة
 */
function updateCartUI() {
    const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);
    
    // تحديث شارة السلة العائمة
    elements.cartBadge.textContent = totalItems;
    elements.cartBadge.classList.toggle('show', totalItems > 0);
    
    // إظهار/إخفاء محتوى السلة
    if (state.cart.length === 0) {
        elements.cartItems.innerHTML = '';
        elements.cartEmpty.style.display = 'flex';
        elements.cartFooter.style.display = 'none';
    } else {
        elements.cartEmpty.style.display = 'none';
        elements.cartFooter.style.display = 'block';
        
        // عرض عناصر السلة
        elements.cartItems.innerHTML = state.cart.map(item => `
            <div class="cart-item" data-id="${item.id}">
                <div class="cart-item-image">
                    <img src="${item.image}" alt="${item.name}">
                </div>
                <div class="cart-item-details">
                    <h4 class="cart-item-title">${item.name}</h4>
                    <span class="cart-item-price">${item.price.toLocaleString()} ر.س</span>
                    <div class="cart-item-actions">
                        <div class="quantity-controls">
                            <button class="quantity-btn" onclick="updateQuantity(${item.id}, -1)">−</button>
                            <span class="quantity-value">${item.quantity}</span>
                            <button class="quantity-btn" onclick="updateQuantity(${item.id}, 1)">+</button>
                        </div>
                        <button class="remove-item-btn" onclick="removeFromCart(${item.id})">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // تحديث المجموع
        const { subtotal, tax, total } = calculateTotals();
        elements.subtotal.textContent = `${subtotal.toLocaleString()} ر.س`;
        elements.tax.textContent = `${tax.toLocaleString()} ر.س`;
        elements.total.textContent = `${total.toLocaleString()} ر.س`;
    }
}

/**
 * فتح/إغلاق السلة
 */
function toggleCart(open) {
    const isOpen = open !== undefined ? open : !elements.cartSidebar.classList.contains('open');
    
    elements.cartSidebar.classList.toggle('open', isOpen);
    elements.cartOverlay.classList.toggle('show', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
}

/**
 * حفظ السلة في التخزين المحلي
 */
function saveCartToStorage() {
    localStorage.setItem('laRomaCart', JSON.stringify(state.cart));
}

/**
 * تحميل السلة من التخزين المحلي
 */
function loadCartFromStorage() {
    const saved = localStorage.getItem('laRomaCart');
    if (saved) {
        try {
            state.cart = JSON.parse(saved);
            updateCartUI();
        } catch (e) {
            state.cart = [];
        }
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
   9. WHATSAPP ORDER - إرسال الطلب عبر واتساب
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * إرسال الطلب عبر واتساب
 */
function sendWhatsAppOrder() {
    if (state.cart.length === 0) {
        showNotification('السلة فارغة!');
        return;
    }
    
    const { subtotal, tax, total } = calculateTotals();
    
    // تجهيز رسالة الطلب
    let message = '🛒 *طلب جديد من لا روما*\n\n';
    message += '═══════════════════════\n\n';
    
    state.cart.forEach((item, index) => {
        message += `*${index + 1}.* ${item.name}\n`;
        message += `   الكمية: ${item.quantity}\n`;
        message += `   السعر: ${(item.price * item.quantity).toLocaleString()} ر.س\n\n`;
    });
    
    message += '═══════════════════════\n\n';
    message += `*المجموع الفرعي:* ${subtotal.toLocaleString()} ر.س\n`;
    message += `*الضريبة (15%):* ${tax.toLocaleString()} ر.س\n`;
    message += `*الإجمالي:* ${total.toLocaleString()} ر.س\n\n`;
    message += '═══════════════════════\n\n';
    message += 'شكراً لطلبكم من لا روما! 🇮🇹';
    
    // رقم الواتساب (يمكنك تغييره)
    const phoneNumber = '966512345678';
    
    // إنشاء رابط واتساب
    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
    
    // فتح واتساب
    window.open(whatsappUrl, '_blank');
}

/* ═══════════════════════════════════════════════════════════════════════════
   10. QR CODE GENERATION - إنشاء QR Code
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * إنشاء QR Code للمنيو الرقمي
 */
function generateQRCode() {
    // رابط المنيو (يمكنك تغييره للرابط الفعلي)
    const menuUrl = window.location.href;
    
    // إنشاء QR Code
    QRCode.toCanvas(menuUrl, {
        width: 180,
        margin: 2,
        color: {
            dark: '#1a1a2e',
            light: '#ffffff'
        }
    }, (error, canvas) => {
        if (error) {
            console.error('Error generating QR Code:', error);
            return;
        }
        
        // إضافة Canvas للصفحة
        elements.qrContainer.innerHTML = '';
        elements.qrContainer.appendChild(canvas);
    });
}

/* ═══════════════════════════════════════════════════════════════════════════
   11. DARK MODE - الوضع الليلي
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * تبديل الوضع الليلي
 */
function toggleDarkMode() {
    state.isDarkMode = !state.isDarkMode;
    document.body.classList.toggle('dark-mode', state.isDarkMode);
    
    // تبديل أيقونات الشمس/القمر
    const moonIcon = document.querySelector('.moon-icon');
    const sunIcon = document.querySelector('.sun-icon');
    
    if (state.isDarkMode) {
        moonIcon.style.display = 'none';
        sunIcon.style.display = 'block';
    } else {
        moonIcon.style.display = 'block';
        sunIcon.style.display = 'none';
    }
    
    saveThemeToStorage();
}

/**
 * حفظ الوضع الليلي في التخزين المحلي
 */
function saveThemeToStorage() {
    localStorage.setItem('laRomaDarkMode', state.isDarkMode);
}

/**
 * تحميل الوضع الليلي من التخزين المحلي
 */
function loadThemeFromStorage() {
    const saved = localStorage.getItem('laRomaDarkMode');
    if (saved === 'true') {
        state.isDarkMode = true;
        document.body.classList.add('dark-mode');
        
        const moonIcon = document.querySelector('.moon-icon');
        const sunIcon = document.querySelector('.sun-icon');
        moonIcon.style.display = 'none';
        sunIcon.style.display = 'block';
    } else if (saved === null && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        state.isDarkMode = true;
        document.body.classList.add('dark-mode');
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
   12. UI HELPERS - مساعدين الواجهة
   ═══════════════════════════════════════════════════════════════════════════ */

/**
 * إظهار إشعار
 */
function showNotification(text) {
    elements.notificationText.textContent = text;
    elements.notification.classList.add('show');
    
    setTimeout(() => {
        elements.notification.classList.remove('show');
    }, 2500);
}

/* ═══════════════════════════════════════════════════════════════════════════
   13. EVENT LISTENERS - مستمعي الأحداث
   ═══════════════════════════════════════════════════════════════════════════ */

function initEventListeners() {
    // التصنيفات الرئيسية
    document.querySelectorAll('.main-cat-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            filterByCategory(btn.dataset.mainCategory);
        });
    });
    
    // البحث
    elements.searchInput.addEventListener('input', (e) => handleSearch(e.target.value));
    elements.searchClear.addEventListener('click', clearSearch);
    
    // السلة العائمة
    elements.floatingCart.addEventListener('click', () => toggleCart(true));
    elements.cartClose.addEventListener('click', () => toggleCart(false));
    elements.cartOverlay.addEventListener('click', () => toggleCart(false));
    elements.checkoutBtn.addEventListener('click', sendWhatsAppOrder);
    elements.clearCartBtn.addEventListener('click', clearCart);
    
    // الوضع الليلي
    elements.themeToggle.addEventListener('click', toggleDarkMode);
    
    // إغلاق السلة بمفتاح Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (elements.cartSidebar.classList.contains('open')) {
                toggleCart(false);
            }
        }
    });
}

// تهيئة التطبيق عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', init);
