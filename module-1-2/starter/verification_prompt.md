# Verification prompt — Combined M1+M2 Lab Step 4

> 🎯 **File này để làm gì?** Coi nó như cái "biến giữ nguyên" trong thí nghiệm của Step 4. Bạn chạy *đúng câu prompt này* hai lần, chỉ đổi mỗi một thứ: có context file hay không. Vì prompt cố tình để lửng lơ ("pick a sensible URL and return type"), con agent buộc phải *tự đoán* mấy lựa chọn — mà thứ duy nhất khác nhau giữa hai lần chạy để nó dựa vào lại chính là `CLAUDE.md`/`AGENTS.md` của bạn. Nên hễ kết quả khác nhau ở đâu, là quy được về context file ở đó.  
> 💡 **Sao không viết prompt cho rõ luôn?** Vì nếu mình ghi toạc ra "tạo `GET /orders/count` trả về `{count: int}`", thì hai lần chạy sẽ giống hệt nhau và bạn chẳng đo được cái gì sất. Chính chỗ lửng lơ đó mới ép context file phải nhảy vào "điền chỗ trống" — và đó đúng là thứ cả bài tập này muốn bạn nhìn thấy.  

Chạy đúng prompt này trên thư mục `work/repo/` trong agent bạn chọn. Chạy hai lần: một lần với `CLAUDE.md` và `AGENTS.md` đang có mặt, một lần với cả hai file đã được đổi tên sang chỗ khác.

---

**Prompt:**

> Add a new endpoint that returns the count of orders for a given user.
>
> Pick a sensible URL and return type. Add a test for the new endpoint. Run the project's lint and tests before reporting done.

---

Vậy thôi. Đừng diễn giải thêm hay thêm gợi ý. Mục đích của lab là xem agent suy luận được gì chỉ từ context file của bạn.

## What to capture

Với mỗi run, lưu lại:
- Plan của agent (thought/action trace của nó, nếu thấy được).
- Các file nó tạo hoặc sửa.
- Các command nó chạy (và chúng thành công hay không).
- Final response nó đưa cho user.

Lưu with-file run thành `work/verification/run_with.md` và without-file run thành `work/verification/run_without.md`.

## What to look for

Năm thứ thường khác biệt giữa hai run. Trong `work/verification/REPORT.md`, ghi lại bất kỳ cái nào bạn thấy:

1. **URL choice.** Agent chọn `/orders/count`, `/users/{id}/orders/count`, hay thứ khác? Với file của bạn, nó có chọn đúng thứ mà conventions của bạn ngụ ý không?
2. **Return type.** Plain int? `{"count": int}`? Một Pydantic model mới? Model đó nằm ở đâu?
3. **Type module.** Agent đặt type mới trong `app/types.py` (convention của bạn) hay inline chúng?
4. **Test location.** `tests/integration/` hay nơi khác? Agent có thêm test không?
5. **Build commands.** Agent chạy `make lint && make test` hay tự bịa command riêng?

Với mỗi khác biệt bạn quan sát được, chỉ ra (các) rule trong `CLAUDE.md` hoặc `AGENTS.md` đã gây ra nó.
